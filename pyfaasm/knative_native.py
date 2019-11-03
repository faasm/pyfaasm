import os
from json import dumps

from flask import Flask, request

from pyfaasm.core import getOutput, setLocalInputOutput, getCallStatus, setEmulatorMessage

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def run_func():
    json_data = request.get_json()
    return handle_message(json_data)


def handle_message(json_data):
    if json_data.get("status"):
        return _handle_status(json_data)
    else:
        return _handle_call(json_data)


def _handle_status(json_data):
    call_id = json_data["id"]
    print("Status request for {}".format(call_id))
    return getCallStatus(call_id)


def _handle_call(json_data):
    # Set up the emulator
    setEmulatorMessage(dumps(json_data))

    user = json_data["py_user"]
    func = json_data["py_func"]
    idx = json_data.get("py_idx", 0)

    print("Executing {}/{} (idx {})".format(user, func, idx))

    # Assume function is in the current path
    module_name = "pyfaasm.{}.{}".format(user, func)
    mod = __import__(module_name, fromlist=[""])

    # TODO - if asynchronous, run the function in the background
    if json_data.get("async", False):
        # Use emulator to dispatch in the background
        pass
    else:
        # Run the function
        mod.main_func()

    # Return the output
    func_output = getOutput()
    if not func_output:
        return "Empty output"
    else:
        return func_output


if __name__ == "__main__":
    setLocalInputOutput(True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
