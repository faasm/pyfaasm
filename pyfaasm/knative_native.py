import os

from flask import Flask, request

from pyfaasm.core import setFunctionIdx, setInput, getOutput, setLocalInputOutput

app = Flask(__name__)


@app.route('/')
def run_func():
    json_data = request.get_json()
    return handle_message(json_data)


def handle_message(json_data):
    user = json_data["py_user"]
    func = json_data["py_func"]
    idx = json_data.get("py_idx", 0)
    input_data = json_data["input_data"]

    print("Executing {}/{} (idx {}) with input {}".format(user, func, idx, input_data))

    # Assume function is in the current path
    module_name = "pyfaasm.{}.{}".format(user, func)
    mod = __import__(module_name, fromlist=[""])

    # Set up input
    setInput(input_data)

    # Set up the function index and run
    setFunctionIdx(idx)
    mod.main_func()

    # Return the output
    return getOutput()


if __name__ == "__main__":
    setLocalInputOutput(True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
