# General
from flask import Flask, request, jsonify

# For fashionMNIST_MLP()
from tensorflow.keras.datasets import fashion_mnist
import time
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import InputLayer, Flatten, Dense
from tensorflow.keras.optimizers import SGD
import numpy as np

# For stateless redis example
import redis
import os

app = Flask(__name__)

'''
Simple return function for HTTP GET
'''
@app.route("/", methods=['GET']) # or simply: @app.get("/")
def simpleGET():
    who = request.args.get("who", default="World")
    return      f"Hello {who}!\nWelcome to a short demo on " \
                "elasticity and state in cloud native applications.\n"


'''
Algorithm to find the first "Perfect Numbers".
Note: This is a non-optimized approach for demonstration purposes.

A number is called a Perfect Number ("Vollkommende Zahl") if its 
value is equal to the sum of all its integer divisors (excluding itself). 
The first two perfect numbers are
6 = 3 + 2 + 1 and 28 = 14 + 7 + 4 + 2 + 1

Further note:
Euclid proved that 2^(k-1)*(2^k-1) is a perfect number, whenever 
(2^k-1) is a prime number. This means that the search for perfect 
numbers can be reduced to the search for prime numbers 
and a more efficient algorithm can be developed.
'''
@app.route("/perfectNr", methods=['GET'])
def perfectNr():

    number = 1
    perfect_numbers = []
    howMany = int(request.args.get("howMany", default="2"))

    while len(perfect_numbers) < howMany:
        number += 1
        checkSum = 1  # Teiler 1 always included

        for teiler in range(2, number):
            if number % teiler == 0:
                checkSum += teiler

        if checkSum == number:
            perfect_numbers.append(number)

    return jsonify({'perfect numbers': perfect_numbers})


'''
Multi-layer perceptron (MLP) neural network model
with Keras using 'Fashion MNIST' data.
'''
@app.route("/fashionMNIST_MLP", methods=['GET'])
def fashionMNIST_MLP():
    (features_train, labels_train), (features_test, labels_test) = fashion_mnist.load_data()

    # preprocess data
    x_train = features_train.astype('float32') / 255
    x_test = features_test.astype('float32') / 255

    y_train = keras.utils.to_categorical(labels_train, 10) # convert labels' vector to probability matrix
    y_test = keras.utils.to_categorical(labels_test, 10)

    # fix random seed for reproducibility
    seed = 7
    np.random.seed(seed)

    # configure model
    model = Sequential()
    model.add(InputLayer(shape=(28, 28))) # rows, cols
    model.add(Flatten())
    model.add(Dense(units=200, activation='sigmoid'))
    model.add(Dense(units=10, activation='softmax'))

    model.compile(loss = 'categorical_crossentropy', optimizer = SGD(learning_rate=0.1), metrics = ['accuracy'])
    model.summary()

    # train and test model
    start_time = time.time()

    epochs = int(request.args.get("epochs", default="10"))
    batch_size = int(request.args.get("batch_size", default="50"))
    training = model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(x_test, y_test), verbose=1)

    training_time = time.time() - start_time

    # make class predictions with the model
    predictions = model.predict(x_test)

    # collect the first 10 data samples
    labels = {0: 'T-shirt/top', 1: 'Trouser', 2: 'Pullover', 3: 'Dress', 4: 'Coat', 5: 'Sandal', 6: 'Shirt', 7: 'Sneaker', 8: 'Bag', 9: 'Ankle boot'}
    preds = []
    actuals = []
    for i in range(10):
        preds.append(labels[np.argmax(predictions[i])])
        actuals.append(labels[np.argmax(y_test[i])])

    return jsonify({'Training time (in s):': training_time, 
                    'Train accuracy:': training.history['accuracy'][len(training.history['accuracy'])-1],
                    'Train loss:': training.history['loss'][len(training.history['loss'])-1],
                    'Test accuracy:': training.history['val_accuracy'][len(training.history['val_accuracy'])-1],
                    'Test loss:': training.history['val_loss'][len(training.history['val_loss'])-1],
                    'Predictions of the first 10 classes within test:': preds,
                    'Actuals of the first 10 classes within test:': actuals
                    })

'''
Demonstating a statefull component using local memory 
of the instance serving the application
'''
card = []
@app.route("/get_cart_SF", methods=['GET'])
def getCart_SF():
    return jsonify(cart) # return list into a JSON response

@app.route("/add_to_cart_SF", methods=['POST'])
def addToCart_SF():
    cartItem = request.json.get("item") # Assumption: sending JSON data with 'item' key

    if cartItem:
        card.append(cartItem)
        return jsonify(
            {
                'status': 'success',
                'message': 'Item added to cart',
                'cart': cart
            }
        )
    else:
        return jsonify(
            {
                'status': 'error',
                'message': 'No item found in the request'
            }
        ), 400

'''
Demonstating a stateless component using redis in-memory database 
independant of the instance serving the application
'''
# Your instance's IP address and port can be found unter connection 
# properties of the redis instance
redis_host = os.environ.get("REDISHOST", "localhost")
redis_port = int(os.environ.get("REDISPORT", 6379))
redis_db = redis.Redis(host=redis_host, port=redis_port, db=0)
# https://cloud.google.com/memorystore/docs/redis/connect-redis-instance-cloud-run#python
#redis_db = redis.StrictRedis(host=redis_host, port=redis_port)

@app.route("/get_cart_SL", methods=['GET'])
def getCart_SL():
    cart = redis_db.lrange('cart', 0, -1) # get all items from the list
    cart = [item.decode('utf-8') for item in cart] # convert bytes to string
    return jsonify(cart) # return list into a JSON response

@app.route("/add_to_cart_SL", methods=['POST'])
def addToCart_SL():
    cartItem = request.json.get("item") # Assumption: sending JSON data with 'item' key

    if cartItem:
        redis_db.rpush('cart', cartItem) # Push item to 'cart' list in Redis
        cart = redis_db.lrange('cart', 0, -1) # get all items from the list
        cart = [item.decode('utf-8') for item in cart] # convert bytes to string
        return jsonify(
            {
                'status': 'success',
                'message': 'Item added to cart',
                'cart': cart
            }
        )
    else:
        return jsonify(
            {
                'status': 'error',
                'message': 'No item found in the request'
            }
        ), 400
    
if __name__ == "__main__":
    # Testing:
    # run "pip install -r requirements.txt"
    # run "python main.py" 
    # open "http://localhost:8080"
    # Deployment:
    # When deploying to Cloud Run, a production-grade WSGI HTTP server,
    # such as Gunicorn, will serve the app.
    app.run(host="localhost", port=8080, debug=True)