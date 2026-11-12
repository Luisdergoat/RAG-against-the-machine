import re


def tokenize(text: str) -> list[str]:
    tokens = []
    tokens = re.findall(r"[A-Za-z0-9_]+", text)

    temp = []
    for word in tokens:
        hit = re.search(r"_", word)
        if hit:
            sub_tokens = re.split(r"_+", word)
            temp.append(word)
            for sub_token in sub_tokens:
                if sub_token:
                    temp.append(sub_token)
        else:
            temp.append(word)

    result = []
    pattern = r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+"
    for token in temp:
        if "_" in token:
            result.append(token)
            continue
        sub_tokens = re.findall(pattern, token)
        if len(sub_tokens) > 1:
            result.append(token)
        for sub_token in sub_tokens:
            result.append(sub_token)

    for i in range(len(result)):
        result[i] = result[i].lower()

    return result
