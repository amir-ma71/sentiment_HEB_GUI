from flask import Flask, request, jsonify
import pickle
from keras.models import load_model
from keras.preprocessing import sequence
from langdetect import detect, DetectorFactory
import src.pre_pro
import tensorflow as tf

# for handeling of loading model just once not each request
global graph
graph = tf.get_default_graph()

# loading model and tokens file
with open('./src/tokens.pickle', 'rb') as handle:
    tokenize = pickle.load(handle)
model = load_model("./src/model.h5")

# tokenizer
def tokenizer(x, vocabulary_size=5000, char_level=True):
    tok = []
    x_ = tokenize.texts_to_sequences(x)
    for i in x_:
        tok = tok + i

    return [tok]

# padding sequence
def pad(x, max_document_length=300):
    x_ = sequence.pad_sequences(x, maxlen=max_document_length, padding='post', truncating='post')
    return x_

# prepare input and predict sentiment from model
def prepare_input(sent):
    vector = pad(tokenizer(sent))
    with graph.as_default():
        sent_pred = model.predict(vector)

    return sent_pred


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/predict', methods=['POST'])
def prepare_text():

    # get sent from user online
    request_data = request.get_json()

    input_sent = request_data['sentence']

    # preprocessing sent
    # remove all char except Heb words
    sent = src.pre_pro.stop_word_remover(src.pre_pro.tokenize(input_sent), is_split=True, return_split=False)

    # Detect language of text
    try:
        DetectorFactory.seed = 0
        lang = detect(sent)
    except:
        return "No text enter"

    if lang != "he":
        return "the language is not Hebrew, please type Hebrew language to detect topic."

    if not sent:
        return

    if len(sent) < 20:
        return "your text is too small, please type more words to detect"

    # Prepare the text
    prediction_dataloader = prepare_input(sent)

    label_list = ["Positive", "negetive"]
    final_dict = {}

    # build json of predict as label_list
    for i in range(len(label_list)):
        final_dict[label_list[i]] = str(prediction_dataloader[0][i])

    # sorting
    final_dict = {k: v for k, v in sorted(final_dict.items(), key=lambda item: item[1], reverse=True)}

    print("sent: ", sent)
    print("label: ",final_dict)

    # Return on a JSON format
    return jsonify(final_dict)


@app.route('/check', methods=['GET'])
def check():
    return "every things right! "


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
