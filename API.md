Request:

```py
import httpx

url = "https://translate.kagi.com/api/proofread"
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-signal": "abortable",
    "Referer": "https://translate.kagi.com/proofread"
}
data = {
    "text": "co",
    "source_lang": "auto",
    "session_token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWJzY3JpcHRpb24iOnRydWUsImlkIjoiNDg5NjM0IiwibG9nZ2VkSW4iOnRydWUsInRoZW1lIjpudWxsLCJtb2JpbGVUaGVtZSI6bnVsbCwiY3VzdG9tQ3NzRW5hYmxlZCI6dHJ1ZSwibGFuZ3VhZ2UiOm51bGwsImN1c3RvbUNzc0F2YWlsYWJsZSI6ZmFsc2UsImFjY291bnRUeXBlIjoicHJvZmVzc2lvbmFsIiwiaWF0IjoxNzU5MTUxNTMzLCJleHAiOjE3NTkxNTc1MzN9.DfRx0xYBKmrY03waqSku3ENlQNZCZVAlK0Qw9JeQmQw",
    "model": "standard",
    "stream": True,
    "writing_style": "general",
    "correction_level": "standard",
    "formality": "default",
    "context": "",
    "explanation_language": "en"
}

response = httpx.post(url, headers=headers, json=data)
print(response.text)
```


Response:

```
event: message
data: {"detected_language":{"iso":"ro","label":"Romanian"}}

event: message
data: {"delta":"co"}

event: message
data: {"text_done":true}

event: message
data: {"analysis":{"corrected_text":"co","changes":[],"corrections_summary":"No corrections were needed.","tone_analysis":{"overall_tone":"neutral","description":"The input is a two-letter fragment ('co') and contains no clear lexical, syntactic, or emotional cues to establish a distinct tone. It is too short to exhibit formality, informality, or emotional stance."},"voice_consistency":{"active_voice_percentage":0,"passive_voice_percentage":0,"is_consistent":true,"passive_instances":[],"summary":"No complete clauses are present, so active or passive voice cannot be identified. The fragment is neutral with respect to voice."},"repetition_detection":{"repeated_words":[],"repeated_phrases":[],"summary":"The text is a single short fragment with no repeated words or phrases."},"writing_statistics":{"word_count":1,"character_count":2,"character_count_no_spaces":2,"paragraph_count":1,"sentence_count":1,"average_words_per_sentence":1,"average_characters_per_word":2,"sentence_length_distribution":{"short":1,"medium":0,"long":0},"vocabulary_diversity":1,"reading_time_minutes":0.1,"complex_sentences":0,"simple_sentences":1,"reading_level":"elementary","readability_score":20},"explanation_language":"en"}}

event: message
data: {"done":true}
```


## Auth


````python
import httpx

url = "https://translate.kagi.com/api/auth"
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=1, i",
    "referer": "https://translate.kagi.com/proofread?from=auto&text=The+decryptiohn+runtine+would+be+cool+so+we+could+decode+the+command+from+the+git+%3Aface_with_rolling_eyes%3A+",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}
cookies = {
    "kagi_session": "UwY9QN9CziikpU5KF_FEZhDFML9EVOpWbzWHlOV0pzc.yX9fVSXCE2pRklLJTStDTcM2ojqFbwHYOw0SWuj_1Co",
    "translate_custom_css_enabled": "true",
    "target_lang": "fr",
    "quality": "best",
    "translate_session": "eyJhbGciOiJIUzI1NiJ9.eyJzdWJzY3JpcHRpb24iOnRydWUsImlkIjoiNDg5NjM0IiwibG9nZ2VkSW4iOnRydWUsInRoZW1lIjpudWxsLCJtb2JpbGVUaGVtZSI6bnVsbCwiY3VzdG9tQ3NzRW5hYmxlZCI6dHJ1ZSwibGFuZ3VhZ2UiOm51bGwsImN1c3RvbUNzc0F2YWlsYWJsZSI6ZmFsc2UsImFjY291bnRUeXBlIjoicHJvZmVzc2lvbmFsIiwiaWF0IjoxNzU5MTUxNTMzLCJleHAiOjE3NTkxNTc1MzN9.DfRx0xYBKmrY03waqSku3ENlQNZCZVAlK0Qw9JeQmQw",
    "source_lang": "en"
}

response = httpx.get(url, headers=headers, cookies=cookies)
print(response.text)
````

### Response

Token refresh every 200 seconds

```json
{
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWJzY3JpcHRpb24iOnRydWUsImlkIjoiNDg5NjM0IiwibG9nZ2VkSW4iOnRydWUsInRoZW1lIjpudWxsLCJtb2JpbGVUaGVtZSI6bnVsbCwiY3VzdG9tQ3NzRW5hYmxlZCI6dHJ1ZSwibGFuZ3VhZ2UiOm51bGwsImN1c3RvbUNzc0F2YWlsYWJsZSI6ZmFsc2UsImFjY291bnRUeXBlIjoicHJvZmVzc2lvbmFsIiwiaWF0IjoxNzU5MTUxNTMzLCJleHAiOjE3NTkxNTc1MzN9.DfRx0xYBKmrY03waqSku3ENlQNZCZVAlK0Qw9JeQmQw",
    "id": "489634",
    "loggedIn": true,
    "subscription": true,
    "expiresAt": "2025-09-29T14:52:13.000Z",
    "theme": "",
    "mobileTheme": "",
    "customCssEnabled": true,
    "language": "en",
    "customCssAvailable": false,
    "accountType": "professional"
}
```

JWT 

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWJzY3JpcHRpb24iOnRydWUsImlkIjoiNDg5NjM0IiwibG9nZ2VkSW4iOnRydWUsInRoZW1lIjpudWxsLCJtb2JpbGVUaGVtZSI6bnVsbCwiY3VzdG9tQ3NzRW5hYmxlZCI6dHJ1ZSwibGFuZ3VhZ2UiOm51bGwsImN1c3RvbUNzc0F2YWlsYWJsZSI6ZmFsc2UsImFjY291bnRUeXBlIjoicHJvZmVzc2lvbmFsIiwiaWF0IjoxNzU5MTUxNTMzLCJleHAiOjE3NTkxNTc1MzN9.DfRx0xYBKmrY03waqSku3ENlQNZCZVAlK0Qw9JeQmQw
```


````python
import jwt

token = "your_token_here"
secret = "your_secret_here"

decoded = jwt.decode(token, secret, algorithms=["HS256"])
print(decoded)
````

```py
import jwt
token="eyJhbGciOiJIUzI1NiJ9.eyJzdWJzY3JpcHRpb24iOnRydWUsImlkIjoiNDg5NjM0IiwibG9nZ2VkSW4iOnRydWUsInRoZW1lIjpudWxsLCJtb2JpbGVUaGVtZSI6bnVsbCwiY3VzdG9tQ3NzRW5hYmxlZCI6dHJ1ZSwibGFuZ3VhZ2UiOm51bGwsImN1c3RvbUNzc0F2YWlsYWJsZSI6ZmFsc2UsImFjY291bnRUeXBlIjoicHJvZmVzc2lvbmFsIiwiaWF0IjoxNzU5MTUxNTMzLCJleHAiOjE3NTkxNTc1MzN9.DfRx0xYBKmrY03waqSku3ENlQNZCZVAlK0Qw9JeQmQw"
jwt.decode(token, "secret",algorithms=["HS256"], options={"verify_signature": False})
# {'subscription': True, 'id': '489634', 'loggedIn': True, 'theme': None, 'mobileTheme': None, 'customCssEnabled': True, 'language': None, 'customCssAvailable': False, 'accountType': 'professional', 'iat': 1759151533, 'exp': 1759157533}
```

```json
{'subscription': True, 'id': '489634', 'loggedIn': True, 'theme': None, 'mobileTheme': None, 'customCssEnabled': True, 'language': None, 'customCssAvailable': False, 'accountType': 'professional', 'iat': 1759151533, 'exp': 1759157533}
```
