from Crypto.PublicKey import RSA


PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\n" \
              "MIIEogIBAAKCAQEAiY2JBgMV90ULt0btku198l6wGuzn3xCcHs+eBZHL2C+XWRA3\n" \
              "BVDThSBj19dKXehfDphQ5u/Omfm76ImajEPHGBiYtZT7AgcO15zvm+JCpbREbdOV\n" \
              "QkST3ANyqCzi+Fk0ZWRwXQTR9m64ML++42iK0BESUbbrVnKipZJ1tE73xs1XBM8J\n" \
              "DCOIdM2VBVdDArNJZHGzqugEbDzwh0SqEsKYLE7uzst+eY9vIAbyX80pNzC/d1J8\n" \
              "3Pia5WvRV0gtllkMXlGnTIortDJuEr496a8UqfPWDWNg4scCca6aSk/13Q8ClEbP\n" \
              "X1sdW4s9yW9OmGg0VMZj+Tca3Jls/3FJosH0yQIDAQABAoIBADVdDGihr9bjGX17\n" \
              "7dUPf8oUg/ueJwJ5/idR4ntEqbFwHSY3TTEpvzWpcDKfWkF+UcpmuxQsupkvsn+v\n" \
              "Sp7Z+JZXjH79kjeiJ1bskmSGbda9TcLRz9kKo9Y6HDQ0XcV9Tf977L+ZjB8vqxN2\n" \
              "gAbXWusHhHThIwHBrWnQnQtbi3K7SzVT3OK0WFfsoAZgYSzfS+4LE0Gs9+ZcK8q7\n" \
              "So4BE7/jSjf+Baux92Hes5spi73ltx/BsyEYR5XQVzWfIUg4sX3VDRbpBTW+DBqA\n" \
              "G0kUh3CjlsPkZeRSiPrAfk610hQr4HLInGxPkaK+8Fuui2ofM0qYwOeGkNXqlY4Z\n" \
              "huhXcFUCgYEAtX0/KoF9k52FbSJdl+2ekeBluU9fJyB3SpGyk5MTKeoAo9I82KyJ\n" \
              "tens+5ebj8rUZYHTQfjHsm0ihy4F3GH+huPw4B+RQ8h5BLkU5+KC6pT60M+eMj13\n" \
              "bJZkm9n4bInDx9f8Aj4XSG+P2g8h9dBSSm4Ewiqp4CtFTY58uujvMu8CgYEAwgaE\n" \
              "5vanfxfk08qvZ7WSxUGfZxp6R2sLjfyB2qL4XJk/8ZpLB17kpYdGhhpk5qWRNmlH\n" \
              "vetLp3RZoZRB0JJYq++IkiIq1gfnghgKcSbM8sMXvIT0icBXZU/XTzBVReeRYf9P\n" \
              "Sjc+zD/W6L2lXhdZ7z1rGHHvEH/bMQEj3vIQc8cCgYAN6awN9h9KUakI1LmYC/87\n" \
              "75fcvNjuhu6eKM0nwv6VF/s0k8lWUuO7rlMcdmLWgxYFMg6f4BJu+y7KbhzE6D46\n" \
              "2P5+L+1S5OtiEU4o+JRQp1sS5teZwlyFVoIf8HW63FTF3SjUgy4Fv4enj8Fqtq2Y\n" \
              "RxbWS676IFcPuvyU14Z+wQKBgARZWw9GRhjeMz3gFDBx7HlJcEZCXK1PI/Ipz8tT\n" \
              "zdddhAZpW/ctVFi1gIou+0YEPg4HLBmAtbBqNjwd85+2OBCajOghpe4oPTM4ULua\n" \
              "kAt8/gI2xLh1vD/EG2JmBfNMLoEQ1Pkn5dt0LuAGqDdEtLpdGRJyM1aeVw5xJRmx\n" \
              "OVcvAoGAO2keIaA0uB9SszdgovK22pzmkluCIB7ldcjuf/zkjt62nSOOa3mtEAue\n" \
              "t/b5Jw+yQVBqNkfJwOMykCxcYs4IEuJelbOYSCp3GmW014nDxYbe5y1Q40drdTro\n" \
              "w6Y5FnjFw022w+M3exyH6ZtxcmG6buDbp2F/SPD/FnYy5IFCDig=\n" \
              "-----END RSA PRIVATE KEY-----"


def get_dummy_private_key():
    return RSA.importKey(PRIVATE_KEY)
