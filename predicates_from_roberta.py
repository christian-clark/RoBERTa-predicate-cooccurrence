import argparse, torch
from nltk.stem import WordNetLemmatizer
from transformers import AutoTokenizer, RobertaForMaskedLM


MASK_ID = 50264

TEMPLATES = {
    "adj": "One of them is very <mask>.",
    "noun": "The child saw the <mask>.",
    "vintrans": "One of them will <mask>.",
    "vtrans": "One of them will <mask> another one."
}
    #"noun": "This is the <mask>.",
    #"noun": "Here is a <mask>.",
    #"noun": "I saw the <mask>.",

argparser = argparse.ArgumentParser(
    """
    Extract likely predicates from RoBERTa.
    """
)

argparser.add_argument(
    "pos", choices=["adj", "noun", "vintrans", "vtrans"],
    help="part of speech"
)

argparser.add_argument(
    "-n", type=int, default=50,
    help="number of predicates"
)

argparser.add_argument(
    "-a", "--alphabetize", default=False, action="store_true",
    help="alphabetize results"
)

argparser.add_argument(
    "-s", "--scores", default=False, action="store_true",
    help="output logit scores"
)

# TODO option for model?
#    argparser.add_argument(
#        "-m",
#        "--model",
#        default="125m"
#    )

args = argparser.parse_args()
pos = args.pos

# location of models: /home/clark.3664/.cache/huggingface/hub/models--roberta-base/snapshots/bc2764f8af2e92b6eb5679868df33e224075ca68
tokenizer = AutoTokenizer.from_pretrained("roberta-base")
model = RobertaForMaskedLM.from_pretrained("roberta-base")
lemmatizer = WordNetLemmatizer()
template = TEMPLATES[pos]

model_input = tokenizer(template, return_tensors="pt")
input_ids = model_input.input_ids[0]
mask_index = input_ids.tolist().index(MASK_ID)
logits = model(**model_input).logits
mask_logits = logits[0, mask_index]
sorted_vals, sorted_indices = torch.sort(mask_logits, descending=True)

words = list()
scores = list()
for v, ix in zip(sorted_vals, sorted_indices):
    word = tokenizer.decode(ix).strip()
    if not word.isalpha(): continue
    if pos == "noun":
        # comparing with lemmatized form ensures that plural nouns
        # aren't included
        lemmatized = lemmatizer.lemmatize(word, pos='n')
        if lemmatized == word:
            words.append(word)
            scores.append(v)
    else:
        words.append(word)
        scores.append(v)
    if len(words) == args.n: break

if args.alphabetize:
    wordscores = sorted(zip(words, scores))
    words = [w for w, s in wordscores]
    scores = [s for w, s in wordscores]

for word, score in zip(words, scores):
    if args.scores:
        print("{}\t{}".format(word, score))
    else:
        print(word)

