/*
 * Copyright (c) 2020 Friedt Professional Engineering Services, Inc
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/logging/log.h>
#include <zephyr/net/net_core.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/tls_credentials.h>
#include <zephyr/posix/unistd.h>
#include <zephyr/sys/util.h>
#include <zephyr/ztest.h>

#include <mbedtls/x509.h>
#include <mbedtls/x509_crt.h>

LOG_MODULE_REGISTER(tls_test, CONFIG_NET_SOCKETS_LOG_LEVEL);

/**
 * @brief An encrypted message to pass between server and client.
 *
 * The answer to life, the universe, and everything.
 *
 * See also <a href="https://en.wikipedia.org/wiki/42_(number)#The_Hitchhiker's_Guide_to_the_Galaxy">42</a>.
 */
#define SECRET "forty-two"

/**
 * @brief Size of the encrypted message passed between server and client.
 */
#define SECRET_SIZE (sizeof(SECRET) - 1)

/** @brief Stack size for the server thread */
#define STACK_SIZE 8192

#define MY_IPV4_ADDR "127.0.0.1"

/** @brief TCP port for the server thread */
#define PORT 4242

/** @brief arbitrary timeout value in ms */
#define TIMEOUT 1000

/**
 * @brief Application-dependent TLS credential identifiers
 *
 * Since both the server and client exist in the same test
 * application in this case, both the server and client credentials
 * are loaded together.
 *
 * The server would normally need
 * - SERVER_CERTIFICATE_TAG (for both public and private keys)
 * - CA_CERTIFICATE_TAG (only when client authentication is required)
 *
 * The client would normally load
 * - CA_CERTIFICATE_TAG (always required, to verify the server)
 * - CLIENT_CERTIFICATE_TAG (for both public and private keys, only when
 *   client authentication is required)
 */
enum tls_tag {
	/** The Certificate Authority public key */
	CA_CERTIFICATE_TAG,
	/** Used for both the public and private server keys */
	SERVER_CERTIFICATE_TAG,
	/** Used for both the public and private client keys */
	CLIENT_CERTIFICATE_TAG,
};

/** @brief synchronization object for server & client threads */
static struct k_sem server_sem;

/** @brief The server thread stack */
static K_THREAD_STACK_DEFINE(server_stack, STACK_SIZE);
/** @brief the server thread object */
static struct k_thread server_thread;

#ifdef CONFIG_TLS_CREDENTIALS
/**
 * @brief The Certificate Authority (CA) Certificate
 *
 * The client needs the CA cert to verify the server public key. TLS client
 * sockets are always required to verify the server public key.
 *
 * Additionally, when the peer verification mode is
 * @ref TLS_PEER_VERIFY_OPTIONAL or @ref TLS_PEER_VERIFY_REQUIRED, then
 * the server also needs the CA cert in order to verify the client. This
 * type of configuration is often referred to as *mutual authentication*.
 */
static const unsigned char ca[] = {
#include "ca.inc"
};

/**
 * @brief The Server Certificate
 *
 * This is the public key of the server.
 */
static const unsigned char server[] = {
#include "server.inc"
};

/**
 * @brief The Server Private Key
 *
 * This is the private key of the server.
 */
static const unsigned char server_privkey[] = {
#include "server_privkey.inc"
};

/**
 * @brief The Client Certificate
 *
 * This is the public key of the client.
 */
static const unsigned char client[] = {
#include "client.inc"
};

/**
 * @brief The Client Private Key
 *
 * This is the private key of the client.
 */
static const unsigned char client_privkey[] = {
#include "client_privkey.inc"
};
#else /* CONFIG_TLS_CREDENTIALS */
#define ca NULL
#define server NULL
#define server_privkey NULL
#define client NULL
#define client_privkey NULL
#endif /* CONFIG_TLS_CREDENTIALS */

/**
 * @brief The server thread function
 *
 * This function simply accepts a client connection and
 * echoes the first @ref SECRET_SIZE bytes of the first
 * packet. After that, the server is closed and connections
 * are no longer accepted.
 *
 * @param arg0 a pointer to the int representing the server file descriptor
 * @param arg1 ignored
 * @param arg2 ignored
 */
static void server_thread_fn(void *arg0, void *arg1, void *arg2)
{
	const int server_fd = POINTER_TO_INT(arg0);
	const int echo = POINTER_TO_INT(arg1);
	const int expect_failure = POINTER_TO_INT(arg2);

	int r;
	int client_fd;
	socklen_t addrlen;
	char addrstr[INET_ADDRSTRLEN];
	struct sockaddr_in sa;
	char *addrstrp;

	k_thread_name_set(k_current_get(), "server");

	NET_DBG("Server thread running");

	memset(&sa, 0, sizeof(sa));
	addrlen = sizeof(sa);

	NET_DBG("Accepting client connection..");
	k_sem_give(&server_sem);
	r = accept(server_fd, (struct sockaddr *)&sa, &addrlen);
	if (expect_failure) {
		zassert_equal(r, -1, "accept() should've failed");
		return;
	}
	zassert_not_equal(r, -1, "accept() failed (%d)", r);
	client_fd = r;

	memset(addrstr, '\0', sizeof(addrstr));
	addrstrp = (char *)inet_ntop(AF_INET, &sa.sin_addr,
				     addrstr, sizeof(addrstr));
	zassert_not_equal(addrstrp, NULL, "inet_ntop() failed (%d)", errno);

	NET_DBG("accepted connection from [%s]:%d as fd %d",
		addrstr, ntohs(sa.sin_port), client_fd);

	if (echo) {
		NET_DBG("calling recv()");
		r = recv(client_fd, addrstr, sizeof(addrstr), 0);
		zassert_not_equal(r, -1, "recv() failed (%d)", errno);
		zassert_equal(r, SECRET_SIZE, "expected: %zu actual: %d",
			      SECRET_SIZE, r);

		NET_DBG("calling send()");
		r = send(client_fd, SECRET, SECRET_SIZE, 0);
		zassert_not_equal(r, -1, "send() failed (%d)", errno);
		zassert_equal(r, SECRET_SIZE, "expected: %zu actual: %d",
			      SECRET_SIZE, r);
	}

	NET_DBG("closing client fd");
	r = close(client_fd);
	zassert_not_equal(r, -1, "close() failed on the server fd (%d)", errno);
}

static int test_configure_server(k_tid_t *server_thread_id, int peer_verify,
				 int echo, int expect_failure)
{
	static const sec_tag_t server_tag_list_verify_none[] = {
		SERVER_CERTIFICATE_TAG,
	};

	static const sec_tag_t server_tag_list_verify[] = {
		CA_CERTIFICATE_TAG,
		SERVER_CERTIFICATE_TAG,
	};

	char addrstr[INET_ADDRSTRLEN];
	const sec_tag_t *sec_tag_list;
	size_t sec_tag_list_size;
	struct sockaddr_in sa;
	const int yes = true;
	char *addrstrp;
	int server_fd;
	int r;

	k_sem_init(&server_sem, 0, 1);

	NET_DBG("Creating server socket");
	r = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
	zassert_not_equal(r, -1, "failed to create server socket (%d)", errno);
	server_fd = r;

	r = setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
	zassert_not_equal(r, -1, "failed to set SO_REUSEADDR (%d)", errno);

	switch (peer_verify) {
	case TLS_PEER_VERIFY_NONE:
		sec_tag_list = server_tag_list_verify_none;
		sec_tag_list_size = sizeof(server_tag_list_verify_none);
		break;
	case TLS_PEER_VERIFY_OPTIONAL:
	case TLS_PEER_VERIFY_REQUIRED:
		sec_tag_list = server_tag_list_verify;
		sec_tag_list_size = sizeof(server_tag_list_verify);

		r = setsockopt(server_fd, SOL_TLS, TLS_PEER_VERIFY,
			       &peer_verify, sizeof(peer_verify));
		zassert_not_equal(r, -1, "failed to set TLS_PEER_VERIFY (%d)",
				  errno);
		break;
	default:
		zassert_true(false, "unrecognized TLS peer verify type %d",
			     peer_verify);
		return -1;
	}

	r = setsockopt(server_fd, SOL_TLS, TLS_SEC_TAG_LIST,
		       sec_tag_list, sec_tag_list_size);
	zassert_not_equal(r, -1, "failed to set TLS_SEC_TAG_LIST (%d)", errno);

	r = setsockopt(server_fd, SOL_TLS, TLS_HOSTNAME, "localhost",
		       sizeof("localhost"));
	zassert_not_equal(r, -1, "failed to set TLS_HOSTNAME (%d)", errno);

	memset(&sa, 0, sizeof(sa));
	/* The server listens on all network interfaces */
	sa.sin_addr.s_addr = INADDR_ANY;
	sa.sin_family = AF_INET;
	sa.sin_port = htons(PORT);

	r = bind(server_fd, (struct sockaddr *)&sa, sizeof(sa));
	zassert_not_equal(r, -1, "failed to bind (%d)", errno);

	r = listen(server_fd, 1);
	zassert_not_equal(r, -1, "failed to listen (%d)", errno);

	memset(addrstr, '\0', sizeof(addrstr));
	addrstrp = (char *)inet_ntop(AF_INET, &sa.sin_addr,
				     addrstr, sizeof(addrstr));
	zassert_not_equal(addrstrp, NULL, "inet_ntop() failed (%d)", errno);

	NET_DBG("listening on [%s]:%d as fd %d",
		addrstr, ntohs(sa.sin_port), server_fd);

	NET_DBG("Creating server thread");
	*server_thread_id = k_thread_create(&server_thread, server_stack,
					    STACK_SIZE, server_thread_fn,
					    INT_TO_POINTER(server_fd),
					    INT_TO_POINTER(echo),
					    INT_TO_POINTER(expect_failure),
					    K_PRIO_PREEMPT(8), 0, K_NO_WAIT);

	r = k_sem_take(&server_sem, K_MSEC(TIMEOUT));
	zassert_equal(0, r, "failed to synchronize with server thread (%d)", r);

	return server_fd;
}

static int test_configure_client(struct sockaddr_in *sa, bool own_cert,
				 const char *hostname)
{
	static const sec_tag_t client_tag_list_verify_none[] = {
		CA_CERTIFICATE_TAG,
	};

	static const sec_tag_t client_tag_list_verify[] = {
		CA_CERTIFICATE_TAG,
		CLIENT_CERTIFICATE_TAG,
	};

	char addrstr[INET_ADDRSTRLEN];
	const sec_tag_t *sec_tag_list;
	size_t sec_tag_list_size;
	char *addrstrp;
	int client_fd;
	int r;

	k_thread_name_set(k_current_get(), "client");

	NET_DBG("Creating client socket");
	r = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
	zassert_not_equal(r, -1, "failed to create client socket (%d)", errno);
	client_fd = r;

	if (own_cert) {
		sec_tag_list = client_tag_list_verify;
		sec_tag_list_size = sizeof(client_tag_list_verify);
	} else {
		sec_tag_list = client_tag_list_verify_none;
		sec_tag_list_size = sizeof(client_tag_list_verify_none);
	}

	r = setsockopt(client_fd, SOL_TLS, TLS_SEC_TAG_LIST,
		       sec_tag_list, sec_tag_list_size);
	zassert_not_equal(r, -1, "failed to set TLS_SEC_TAG_LIST (%d)", errno);

	r = setsockopt(client_fd, SOL_TLS, TLS_HOSTNAME, hostname,
		       strlen(hostname) + 1);
	zassert_not_equal(r, -1, "failed to set TLS_HOSTNAME (%d)", errno);

	sa->sin_family = AF_INET;
	sa->sin_port = htons(PORT);
	r = inet_pton(AF_INET, MY_IPV4_ADDR, &sa->sin_addr.s_addr);
	zassert_not_equal(-1, r, "inet_pton() failed (%d)", errno);
	zassert_not_equal(0, r, "%s is not a valid IPv4 address", MY_IPV4_ADDR);
	zassert_equal(1, r, "inet_pton() failed to convert %s", MY_IPV4_ADDR);

	memset(addrstr, '\0', sizeof(addrstr));
	addrstrp = (char *)inet_ntop(AF_INET, &sa->sin_addr,
				     addrstr, sizeof(addrstr));
	zassert_not_equal(addrstrp, NULL, "inet_ntop() failed (%d)", errno);

	NET_DBG("connecting to [%s]:%d with fd %d",
		addrstr, ntohs(sa->sin_port), client_fd);

	return client_fd;
}
static void test_shutdown(int client_fd, int server_fd, k_tid_t server_thread_id)
{
	int r;

	NET_DBG("closing client fd");
	r = close(client_fd);
	zassert_not_equal(-1, r, "close() failed on the client fd (%d)", errno);

	NET_DBG("closing server fd");
	r = close(server_fd);
	zassert_not_equal(-1, r, "close() failed on the server fd (%d)", errno);

	r = k_thread_join(&server_thread, K_FOREVER);
	zassert_equal(0, r, "k_thread_join() failed (%d)", r);

	k_yield();
}

static void test_common(int peer_verify)
{
	k_tid_t server_thread_id;
	struct sockaddr_in sa;
	uint8_t rx_buf[16];
	int server_fd;
	int client_fd;
	int r;

	/*
	 * Server socket setup
	 */
	server_fd = test_configure_server(&server_thread_id, peer_verify, true,
					  false);

	/*
	 * Client socket setup
	 */
	client_fd = test_configure_client(&sa, peer_verify != TLS_PEER_VERIFY_NONE,
					  "localhost");

	/*
	 * The main part of the test
	 */

	r = connect(client_fd, (struct sockaddr *)&sa, sizeof(sa));
	zassert_not_equal(r, -1, "failed to connect (%d)", errno);

	NET_DBG("Calling send()");
	r = send(client_fd, SECRET, SECRET_SIZE, 0);
	zassert_not_equal(r, -1, "send() failed (%d)", errno);
	zassert_equal(SECRET_SIZE, r, "expected: %zu actual: %d", SECRET_SIZE, r);

	NET_DBG("Calling recv()");
	memset(rx_buf, 0, sizeof(rx_buf));
	r = recv(client_fd, rx_buf, sizeof(rx_buf), 0);
	zassert_not_equal(r, -1, "recv() failed (%d)", errno);
	zassert_equal(SECRET_SIZE, r, "expected: %zu actual: %d", SECRET_SIZE, r);
	zassert_mem_equal(SECRET, rx_buf, SECRET_SIZE,
			  "expected: %s actual: %s", SECRET, rx_buf);

	/*
	 * Cleanup resources
	 */
	 test_shutdown(client_fd, server_fd, server_thread_id);
}

ZTEST(net_socket_tls_api_extension, test_tls_peer_verify_none)
{
	test_common(TLS_PEER_VERIFY_NONE);
}

ZTEST(net_socket_tls_api_extension, test_tls_peer_verify_optional)
{
	test_common(TLS_PEER_VERIFY_OPTIONAL);
}

ZTEST(net_socket_tls_api_extension, test_tls_peer_verify_required)
{
	test_common(TLS_PEER_VERIFY_REQUIRED);
}

static void test_tls_cert_verify_result_opt_common(uint32_t expect)
{
	int server_fd, client_fd, ret;
	k_tid_t server_thread_id;
	struct sockaddr_in sa;
	uint32_t optval;
	socklen_t optlen = sizeof(optval);
	const char *hostname = "localhost";
	int peer_verify = TLS_PEER_VERIFY_OPTIONAL;

	if (expect == MBEDTLS_X509_BADCERT_CN_MISMATCH) {
		hostname = "dummy";
	}

	server_fd = test_configure_server(&server_thread_id, TLS_PEER_VERIFY_NONE,
					  false, false);
	client_fd = test_configure_client(&sa, false, hostname);

	ret = zsock_setsockopt(client_fd, SOL_TLS, TLS_PEER_VERIFY,
			       &peer_verify, sizeof(peer_verify));
	zassert_ok(ret, "failed to set TLS_PEER_VERIFY (%d)", errno);

	ret = zsock_connect(client_fd, (struct sockaddr *)&sa, sizeof(sa));
	zassert_not_equal(ret, -1, "failed to connect (%d)", errno);

	ret = zsock_getsockopt(client_fd, SOL_TLS, TLS_CERT_VERIFY_RESULT,
			       &optval, &optlen);
	zassert_equal(ret, 0, "getsockopt failed (%d)", errno);
	zassert_equal(optval, expect, "getsockopt got invalid verify result %d",
		      optval);

	test_shutdown(client_fd, server_fd, server_thread_id);
}

ZTEST(net_socket_tls_api_extension, test_tls_cert_verify_result_opt_ok)
{
	test_tls_cert_verify_result_opt_common(0);
}

ZTEST(net_socket_tls_api_extension, test_tls_cert_verify_result_opt_bad_cn)
{
	test_tls_cert_verify_result_opt_common(MBEDTLS_X509_BADCERT_CN_MISMATCH);
}

struct test_cert_verify_ctx {
	bool cb_called;
	int result;
};

static int cert_verify_cb(void *ctx, mbedtls_x509_crt *crt, int depth,
			  uint32_t *flags)
{
	struct test_cert_verify_ctx *test_ctx = (struct test_cert_verify_ctx *)ctx;

	test_ctx->cb_called = true;

	if (test_ctx->result == 0) {
		*flags = 0;
	} else {
		*flags |= MBEDTLS_X509_BADCERT_NOT_TRUSTED;
	}

	return test_ctx->result;
}

static void test_tls_cert_verify_cb_opt_common(int result)
{
	int server_fd, client_fd, ret;
	k_tid_t server_thread_id;
	struct sockaddr_in sa;
	struct test_cert_verify_ctx ctx = {
		.cb_called = false,
		.result = result,
	};
	struct tls_cert_verify_cb cb = {
		.cb = cert_verify_cb,
		.ctx = &ctx,
	};

	server_fd = test_configure_server(&server_thread_id, TLS_PEER_VERIFY_NONE,
					  false, result == 0 ? false : true);
	client_fd = test_configure_client(&sa, false, "localhost");

	ret = zsock_setsockopt(client_fd, SOL_TLS, TLS_CERT_VERIFY_CALLBACK,
			       &cb, sizeof(cb));
	zassert_ok(ret, "failed to set TLS_CERT_VERIFY_CALLBACK (%d)", errno);

	ret = zsock_connect(client_fd, (struct sockaddr *)&sa, sizeof(sa));
	zassert_true(ctx.cb_called, "callback not called");
	if (result == 0) {
		zassert_equal(ret, 0, "failed to connect (%d)", errno);
	} else {
		zassert_equal(ret, -1, "connect() should fail");
		zassert_equal(errno, ECONNABORTED, "invalid errno");
	}

	test_shutdown(client_fd, server_fd, server_thread_id);
}

ZTEST(net_socket_tls_api_extension, test_tls_cert_verify_cb_opt_ok)
{
	test_tls_cert_verify_cb_opt_common(0);
}

ZTEST(net_socket_tls_api_extension, test_tls_cert_verify_cb_opt_bad_cert)
{
	test_tls_cert_verify_cb_opt_common(MBEDTLS_ERR_X509_CERT_VERIFY_FAILED);
}

static void *setup(void)
{
	int r;

	/*
	 * Load both client & server credentials
	 *
	 * Normally, this would be split into separate applications but
	 * for testing purposes, we just use separate threads.
	 *
	 * Also, it has to be done before tests are run, otherwise
	 * there are errors due to attempts to load too many certificates.
	 *
	 * The server would normally load
	 * - server public key
	 * - server private key
	 * - ca cert (only when client authentication is required)
	 *
	 * The client would normally load
	 * - ca cert (to verify the server)
	 * - client public key (only when client authentication is required)
	 * - client private key (only when client authentication is required)
	 */
	if (IS_ENABLED(CONFIG_TLS_CREDENTIALS)) {
		NET_DBG("Loading credentials");
		r = tls_credential_add(CA_CERTIFICATE_TAG,
				       TLS_CREDENTIAL_CA_CERTIFICATE,
				       ca, sizeof(ca));
		zassert_equal(r, 0, "failed to add CA Certificate (%d)", r);

		r = tls_credential_add(SERVER_CERTIFICATE_TAG,
				       TLS_CREDENTIAL_PUBLIC_CERTIFICATE,
				       server, sizeof(server));
		zassert_equal(r, 0, "failed to add Server Certificate (%d)", r);

		r = tls_credential_add(SERVER_CERTIFICATE_TAG,
				       TLS_CREDENTIAL_PRIVATE_KEY,
				       server_privkey, sizeof(server_privkey));
		zassert_equal(r, 0, "failed to add Server Private Key (%d)", r);

		r = tls_credential_add(CLIENT_CERTIFICATE_TAG,
				       TLS_CREDENTIAL_PUBLIC_CERTIFICATE,
				       client, sizeof(client));
		zassert_equal(r, 0, "failed to add Client Certificate (%d)", r);

		r = tls_credential_add(CLIENT_CERTIFICATE_TAG,
				       TLS_CREDENTIAL_PRIVATE_KEY,
				       client_privkey, sizeof(client_privkey));
		zassert_equal(r, 0, "failed to add Client Private Key (%d)", r);
	}
	return NULL;
}

ZTEST_SUITE(net_socket_tls_api_extension, NULL, setup, NULL, NULL, NULL);
