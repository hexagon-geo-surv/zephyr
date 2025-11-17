# Copyright (c) 2024 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

'''Runner stub for hardware-robot running on top of real Hardware.'''

import subprocess
import shlex

from runners.core import RunnerCaps, ZephyrBinaryRunner


class HardwareRobotRunner(ZephyrBinaryRunner):
    '''Place-holder for hardware-robot runner customizations.'''

    def __init__(self, cfg, args):
        super().__init__(cfg)
        self.testsuite = args.testsuite
        self.hardware_robot_arg = args.hardware_robot_arg
        self.hardware_robot_help = args.hardware_robot_help

    @classmethod
    def name(cls):
        return 'hardware-robot'

    @classmethod
    def capabilities(cls):
        return RunnerCaps(commands={'robot'}, hide_load_files=True)

    @classmethod
    def do_add_parser(cls, parser):
        parser.add_argument('--testsuite',
                            metavar='SUITE',
                            action='append',
                            default=[],
                            help='path to Robot test suite')
        parser.add_argument('--hardware-robot-arg',
                            metavar='ARG',
                            action='append',
                            default=[],
                            help='additional argument passed to Robot Framework')
        parser.add_argument('--hardware-robot-help',
                            default=False,
                            action='store_true',
                            help='print all possible `hardware-robot` arguments')

    @classmethod
    def do_create(cls, cfg, args):
        return HardwareRobotRunner(cfg, args)

    def do_run(self, command, **kwargs):
        self.run_test(**kwargs)

    def run_test(self, **kwargs):
        cmd = ['robot']

        if self.hardware_robot_help:
            cmd.append('--help')
        else:
            # Add hardware robot arguments
            for arg in self.hardware_robot_arg:
                # Handle arguments that might contain spaces
                cmd.extend(shlex.split(arg))

            # Add test suites
            for suite in self.testsuite:
                cmd.append(suite)

            # Check if we have any test suites to run
            if not self.testsuite:
                self.logger.error("No Robot testsuite passed to Robot Framework! "
                                  "Use the `--testsuite` argument to provide one.")
                return

        # Only run if we have a valid command
        if len(cmd) > 1 or self.hardware_robot_help:
            self.logger.info(f"Running command: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Robot Framework execution failed with return code {e.returncode}")
                raise
            except FileNotFoundError:
                self.logger.error("Robot Framework not found. Please install it with: pip install robotframework")
                raise
        else:
            self.logger.error("No valid command to execute for hardware-robot runner")
