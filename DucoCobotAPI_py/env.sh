sudo chmod 666 /dev/ttyUSB0

#!/bin/bash
CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC2155
export PYTHONPATH=${CURR_DIR}/GripperTestPython:$PYTHONPATH
