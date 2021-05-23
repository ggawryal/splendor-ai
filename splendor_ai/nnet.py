import numpy as np
from tensorflow import keras
from keras import layers
from sklearn.preprocessing import MinMaxScaler

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
        print("training on",len(examples),"examples")

        states = np.array([np.array(ex[0]) for ex in examples]).reshape(len(examples),-1).astype("float32")
        pis = np.array([np.array(ex[1]) for ex in examples]).reshape(len(examples),-1).astype("float32")
        vs = np.array([np.array(ex[2]) for ex in examples]).reshape(len(examples),1).astype("float32")

        self.scaler = MinMaxScaler()
        states = self.scaler.fit_transform(states)

        self.model.fit(
            {"state": states},
            {"pi": pis, "v": vs},
            epochs=3,
            batch_size=32,
        )

    def train_heuristic(self, state_encoder, env):
        examples = []
        
        for s in (0,1):
            for i in range(20):
                for j in range(20):
                    env.reset(False,True)
                    state_vector = state_encoder.state_to_vector(env.return_state())
                    for c1 in range(10):
                        for c2 in range(10):
                            v1,v2 = [0,0,0,0,0], [0,0,0,0,0]
                            for _ in range(c1):
                                v1[np.random.randint(0, 5)] += 1
                            for _ in range(c2):
                                v2[np.random.randint(0, 5)] += 1
                            cards_offset = 7
                            second_player_offset = 34
                            ex = list(state_vector)
                            ex[0] = s
                            ex[1] = i
                            ex[1+cards_offset : 6+cards_offset] = v1
                            ex[second_player_offset] = j
                            ex[second_player_offset+cards_offset : second_player_offset+5+cards_offset] = v2
                            pi = np.ones(self.output_shape)
                            pi /= sum(pi)
                            examples.append((ex,pi, (-1)**s*np.tanh((i*3+c1-j*3-c2)/4)))
        np.random.shuffle(examples)
        self.train(examples)

    def predict(self, state_vector):
        return self.model.predict(self.scaler.transform(np.array(state_vector).reshape(1,-1)))