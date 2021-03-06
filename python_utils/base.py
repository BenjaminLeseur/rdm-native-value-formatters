from abc import ABC, abstractmethod
import binascii
import json
import logging
import sys

from python_utils.helpers import get_arg_parser, wait_for_stdin_value

__version__ = '0.0.1'
DESCRIPTION = 'Python generic formatter'

ACTION_DECODE = 'decode'
ACTION_INFO = 'info'
ACTION_VALIDATE = 'validate'


class BaseFormatter(ABC):
    actions = (ACTION_DECODE, ACTION_INFO, ACTION_VALIDATE)

    def __init__(self, debug=True):
        self.logger = logging.getLogger()

        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    @property
    @abstractmethod
    def description(self):
        return DESCRIPTION

    @property
    @abstractmethod
    def version(self):
        return __version__

    @abstractmethod
    def format(self, value):
        raise NotImplementedError()

    def process_error(self, message):
        if self.action == ACTION_VALIDATE:
            print(json.dumps({
                'valid': False,
                'error': message
            }))
        else:
            self.logger.error(message)
            sys.exit(2)

    def validate_action(self, action):
        if action not in self.actions:
            self.logger.error('Error: Invalid action {}'.format(action))
            sys.exit(1)
        self.action = action

    @staticmethod
    def valid_output():
        print(json.dumps({
            'valid': True,
            'error': ''
        }))

    def info_output(self):
        print(json.dumps({
            'version': self.version,
            'description': self.description
        }))

    @staticmethod
    def formatted_output(output):
        def get_output_dict(output):
            return {
                'output': output,
                'read-only': True,
                'format': 'plain_text',
            }

        if hasattr(output, 'decode'):
            output = output.decode()

        try:
            json_output = json.dumps(get_output_dict(output))
        except (TypeError, OverflowError):
            json_output = json.dumps(get_output_dict(repr(output)))

        print(json_output)

    def main(self, *args):
        parser = get_arg_parser(description=self.description,
                                version=self.version,
                                actions=self.actions)
        if args:
            args = parser.parse_args(args)
        else:
            args = parser.parse_args()

        self.validate_action(args.action)

        if self.action == ACTION_INFO:
            return self.info_output()

        try:
            value = wait_for_stdin_value()
        except binascii.Error as e:
            return self.process_error('Cannot decode value: {}'.format(e))

        if not value:
            return self.process_error('No value to format.')

        try:
            output = self.format(value=value)
        except Exception as e:
            return self.process_error('Cannot format value: {}'.format(e))

        if self.action == ACTION_VALIDATE:
            return self.valid_output()

        return self.formatted_output(output)
