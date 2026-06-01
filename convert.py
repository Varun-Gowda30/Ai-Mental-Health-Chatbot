import tensorflow as tf

model = tf.keras.models.load_model('_mini_XCEPTION.106-0.65.hdf5')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
open("converted_model.tflite", "wb").write(tflite_model)
