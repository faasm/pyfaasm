import os

from flask import Flask, request

from pyfaasm.core import setFunctionIdx, setInput, getOutput, setLocalInputOutput, getCallStatus

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
    user = json_data["py_user"]
    func = json_data["py_func"]
    idx = json_data.get("py_idx", 0)
    input_data = json_data.get("input_data", None)

    print("Executing {}/{} (idx {}) with input {}".format(user, func, idx, input_data))

    # Assume function is in the current path
    module_name = "pyfaasm.{}.{}".format(user, func)
    mod = __import__(module_name, fromlist=[""])

    # Set up input
    if input_data:
        # Convert string to bytes
        setInput(input_data.encode("utf-8"))

    # Set up the function index and run
    setFunctionIdx(idx)
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
