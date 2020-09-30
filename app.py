import numpy as np
from flask import Flask, request, jsonify, json
from sklearn.metrics.pairwise import cosine_similarity
from class_detection import *
app = Flask(__name__)



@app.route('/class_linking/', methods=['POST'])
def cl_func():

    if request.method == 'POST':
        decoded_data = request.data.decode('utf-8')
        params = json.loads(decoded_data)
        vecs = CL(params["NVP"])
        print(vecs)
        return jsonify({'classLinking': vecs})

def cl_func_test(edg):
    return CL(edg)

if __name__ == "__main__":
    app.run(debug=True)