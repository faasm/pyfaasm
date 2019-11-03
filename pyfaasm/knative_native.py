import os
from json import dumps
import threading

from flask import Flask, request

from pyfaasm.core import getOutput, setLocalInputOutput, setEmulatorMessage, emulatorSetStatus, emulatorGetAsyncResponse

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def run_func():
    json_data = request.get_json()
    return handle_message(json_data)


def execute_main(mod):
    mod.main_func()
    emulatorSetStatus(True)


def handle_message(json_data):
    # Set up the emulator
    setEmulatorMessage(dumps(json_data))

    user = json_data["py_user"]
    func = json_data["py_func"]
    idx = json_data.get("py_idx", 0)

    print("Executing {}/{} (idx {})".format(user, func, idx))

    # Assume function is in the current path
    module_name = "pyfaasm.{}.{}".format(user, func)
    mod = __import__(module_name, fromlist=[""])

    if json_data.get("async", False):
        # Use emulator to dispatch in the background
        func_thread = threading.Thread(target=execute_main, args=[mod])
        func_thread.start()

        return emulatorGetAsyncResponse()
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
