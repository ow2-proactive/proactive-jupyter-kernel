import json
import os
import sys
import argparse
import logging

# import urllib

from jupyter_client.kernelspec import KernelSpecManager
from IPython.utils.tempdir import TemporaryDirectory

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

kernel_json = {"argv": [sys.executable, "-m", "proactive-jupyter-kernel", "-f", "{connection_file}"],
               "display_name": "ProActive",
               "language": "python",
               "codemirror_mode": "python"
               }


def install_my_kernel_spec(user=True, prefix=None):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        kernel_spec_path = os.path.join(td, 'kernel.json')
        logging.debug(f'Writing kernel spec to {kernel_spec_path}')
        with open(kernel_spec_path, 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)
        # TODO: Copy resources once they're specified
        # Uncomment and update this section to download resources
        # git_url = "https://raw.githubusercontent.com/ow2-proactive/proactive-jupyter-kernel/master/proactive-jupyter-kernel/"
        # for size in ['32', '64', '128']:
        #     urllib.request.urlretrieve(f"{git_url}/logo-{size}x{size}.png", os.path.join(td, f'logo-{size}x{size}.png'))
        logging.info('Installing IPython kernel spec')
        try:
            KernelSpecManager().install_kernel_spec(td, 'ProActive', user=user, prefix=prefix)
            logging.info('Successfully installed ProActive kernel!')
        except Exception as e:
            logging.error(f'Error installing kernel spec: {str(e)}')
            raise


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        logging.debug('Non-Unix platform, assuming not admin')
        return False  # assume not an admin on non-Unix platforms


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Install KernelSpec for ProActive Kernel'
    )
    prefix_locations = parser.add_mutually_exclusive_group()
    prefix_locations.add_argument(
        '--user',
        help='Install KernelSpec in user home directory',
        action='store_true'
    )
    prefix_locations.add_argument(
        '--sys-prefix',
        help='Install KernelSpec in sys.prefix. Useful in conda / virtualenv',
        action='store_true',
        dest='sys_prefix'
    )
    prefix_locations.add_argument(
        '--prefix',
        help='Install KernelSpec in this prefix',
        default=None
    )
    args = parser.parse_args(argv)
    user = args.user or not _is_root()
    prefix = args.prefix or (sys.prefix if args.sys_prefix else None)
    if prefix:
        logging.info(f'Installing with prefix at {prefix}')
    elif user:
        logging.info('Installing for user')
    try:
        install_my_kernel_spec(user=user, prefix=prefix)
    except Exception as e:
        logging.error(f'Installation failed: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
