import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Predictor:
    def __init__(self):
        model_name = "cointegrated/rubert-tiny-toxicity"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

    def predict(self, text: str) -> tuple[str, float]:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        toxic_score = float(probs[1])
        if toxic_score >= 0.5:
            return "toxic", round(toxic_score, 4)
        else:
            return "neutral", round(1 - toxic_score, 4)
