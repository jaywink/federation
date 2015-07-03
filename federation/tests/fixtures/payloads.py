ENCRYPTED_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <encrypted_header>{encrypted_header}</encrypted_header>
                <content />
            </diaspora>
        """
UNENCRYPTED_DIASPORA_PAYLOAD = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <header>
                    <author_id>bob@example.com</author_id>
                </header>
                <me:env>
                    <me:data type='application/xml'>{data}</me:data>
                    <me:encoding>base64url</me:encoding>
                    <me:alg>RSA-SHA256</me:alg>
                    <me:sig>{signature}</me:sig>
                </me:env>
            </diaspora>
        """
