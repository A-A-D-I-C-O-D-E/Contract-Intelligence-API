# eval/qa_eval.py
import requests, json
DATA = json.load(open("eval/qa_eval_set.json"))
URL = "http://localhost:8000/api/ask"

def run():
    correct = 0
    for q in DATA:
        payload = {"question": q["question"], "document_ids": q.get("document_id")}
        r = requests.post(URL, json=payload)
        res = r.json()
        ans = res.get("answer","").lower()
        expected = q["expected"].lower()
        ok = expected in ans
        print(q["question"], "->", res.get("answer"), "OK?", ok)
        if ok:
            correct += 1
    print("Accuracy:", correct/len(DATA))

if __name__ == "__main__":
    run()
