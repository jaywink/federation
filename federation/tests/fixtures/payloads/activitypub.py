ACTIVITYPUB_FOLLOW = {
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1",
  ],
  "id": "https://example.com/follow",
  "type": "Follow",
  "actor": "https://example.com/actor",
  "object": "https://example.org/actor",
  "signature": {
    "type": "RsaSignature2017",
    "creator": "https://example.com/actor#main-key",
    "created": "2018-10-11T15:59:32Z",
    "signatureValue": "foobar"
  }
}
