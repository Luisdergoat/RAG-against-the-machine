import re


def tokenize(text: str) -> list[str]:
    tokens = []
    current_token = ""
    for char in text:
        if re.match(r"[a-zA-Z0-9_]", char):
            current_token += char
        else:
            if current_token:
                tokens.append(current_token)
                current_token = ""
            if not char.isspace():
                continue  # Skip
    if current_token:
        tokens.append(current_token)

    temp = []
    for word in tokens:
        hit = re.search(r"_", word)
        if hit:
            sub_tokens = re.split(r"(_+)", word)
            temp.append(word)
            for sub_token in sub_tokens:
                if sub_token == "_":
                    continue
                if sub_token:
                    temp.append(sub_token)
        else:
            temp.append(word)

    result = []
    pattern = r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+"
    for token in temp:
        hit = re.search(r"[A-Z]", token)
        if hit:
            sub_tokens = re.findall(pattern, token)
            result.append(token)
            for sub_token in sub_tokens:
                if sub_token:
                    result.append(sub_token)
        else:
            result.append(token)

    for i in range(len(result)):
        result[i] = result[i].lower()

    return result
