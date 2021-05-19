import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras import layers

class NNet:
    def __init__(self, input_shape, output_shape):
        self.input_shape = input_shape
        self.output_shape = output_shape
        inp =  keras.Input(shape=(input_shape),name='state')
        l0 =  layers.Dense(512,activation='sigmoid')(inp)
        pi_pred = layers.Dense(output_shape, activation='softmax',name='pi')(l0)
        v_pred = layers.Dense(1, activation='tanh',name='v')(l0)
        self.model = keras.Model(inputs = [inp], outputs=[pi_pred, v_pred])

        self.model.compile(
            optimizer=keras.optimizers.Adam(1e-3),
            loss=[
                keras.losses.CategoricalCrossentropy(from_logits=True),
                keras.losses.MSE
            ],
            loss_weights=[1.0, 1.0],
        )
    
    def train(self, examples):
        print("training on",examples,"examples")

        states = np.array([np.array(ex[0]) for ex in examples]).reshape(len(examples),-1).astype("float32")
        pis = np.array([np.array(ex[1]) for ex in examples]).reshape(len(examples),-1).astype("float32")
        vs = np.array([np.array(ex[2]) for ex in examples]).reshape(len(examples),1).astype("float32")

        self.model.fit(
            {"state": states},
            {"pi": pis, "v": vs},
            epochs=3,
            batch_size=32,
        )
        input()

    def predict(self, state_vector):
        return self.model.predict(np.array(state_vector).reshape(1,-1))
