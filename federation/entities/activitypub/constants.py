CONTEXT_ACTIVITYSTREAMS = "https://www.w3.org/ns/activitystreams"
CONTEXT_DIASPORA = {"diaspora": "https://diasporafoundation.org/ns/"}
CONTEXT_HASHTAG = {"Hashtag": "as:Hashtag"}
CONTEXT_LD_SIGNATURES = "https://w3id.org/security/v1"
CONTEXT_MANUALLY_APPROVES_FOLLOWERS = {"manuallyApprovesFollowers": "as:manuallyApprovesFollowers"}
CONTEXT_PYTHON_FEDERATION = {"pyfed": "https://docs.jasonrobinson.me/ns/python-federation#"}
CONTEXT_SENSITIVE = {"sensitive": "as:sensitive"}

CONTEXTS_DEFAULT = [
    CONTEXT_ACTIVITYSTREAMS,
    CONTEXT_PYTHON_FEDERATION,
]

CONTEXT = [CONTEXT_ACTIVITYSTREAMS, CONTEXT_LD_SIGNATURES]
CONTEXT_DICT = {}
for ctx in [CONTEXT_DIASPORA, CONTEXT_HASHTAG, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_SENSITIVE, CONTEXT_PYTHON_FEDERATION]:
    CONTEXT_DICT.update(ctx)
CONTEXT.append(CONTEXT_DICT)

NAMESPACE_PUBLIC = "https://www.w3.org/ns/activitystreams#Public"
