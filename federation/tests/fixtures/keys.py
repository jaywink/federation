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

# Not related to above private key
PUBKEY = "-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAuCfU1G5X+3O6vPdSz6QY\nSFbgdbv3KPv" \
         "xHi8tRmlyOLdLt5i1eqsy2WCW1iYNijiCL7OfbrvymBQxe3GA9S64\nVuavwzQ8nO7nzpNMqxY5tBXsBM1lECCHDOvm5dzINXWT9Sg7P1" \
         "8iIxE/2wQEgMUL\nAeVbJtAriXM4zydL7c91agFMJu1aHp0lxzoH8I13xzUetGMutR1tbcfWvoQvPAoU\n89uAz5j/DFMhWrkVEKGeWt1" \
         "YtHMmJqpYqR6961GDlwRuUsOBsLgLLVohzlBsTBSn\n3580o2E6G3DEaX0Az9WB9ylhNeV/L/PP3c5htpEyoPZSy1pgtut6TRYQwC8wns" \
         "qO\nbVIbFBkrKoaRDyVCnpMuKdDNLZqOOfhzas+SWRAby6D8VsXpPi/DpeS9XkX0o/uH\nJ9N49GuYMSUGC8gKtaddD13pUqS/9rpSvLD" \
         "rrDQe5Lhuyusgd28wgEAPCTmM3pEt\nQnlxEeEmFMIn3OBLbEDw5TFE7iED0z7a4dAkqqz8KCGEt12e1Kz7ujuOVMxJxzk6\nNtwt40Sq" \
         "EOPcdsGHAA+hqzJnXUihXfmtmFkropaCxM2f+Ha0bOQdDDui5crcV3sX\njShmcqN6YqFzmoPK0XM9P1qC+lfL2Mz6bHC5p9M8/FtcM46" \
         "hCj1TF/tl8zaZxtHP\nOrMuFJy4j4yAsyVy3ddO69ECAwEAAQ==\n-----END PUBLIC KEY-----\n"

SIGNATURE = "A/vVRxM3V1ceEH1JrnPOaIZGM3gMjw/fnT9TgUh3poI4q9eH95AIoig+3eTA8XFuGvuo0tivxci4e0NJ1VLVkl/aqp8rvBNrRI1RQk" \
            "n2WVF6zk15Gq6KSia/wyzyiJHGxNGM8oFY4qPfNp6K+8ydUti22J11tVBEvQn+7FPAoloF2Xz1waK48ZZCFs8Rxzj+4jlz1PmuXCnT" \
            "j7v7GYS1Rb6sdFz4nBSuVk5X8tGOSXIRYxPgmtsDRMRrvDeEK+v3OY6VnT8dLTckS0qCwTRUULub1CGwkz/2mReZk/M1W4EbUnugF5" \
            "ptslmFqYDYJZM8PA/g89EKVpkx2gaFbsC4KXocWnxHNiue18rrFQ5hMnDuDRiRybLnQkxXbE/HDuLdnognt2S5wRshPoZmhe95v3qq" \
            "/5nH/GX1D7VmxEEIG9fX+XX+Vh9kzO9bLbwoJZwm50zXxCvrLlye/2JU5Vd2Hbm4aMuAyRAZiLS/EQcBlsts4DaFu4txe60HbXSh6n" \
            "qNofGkusuzZnCd0VObOpXizrI8xNQzZpjJEB5QqE2gbCC2YZNdOS0eBGXw42dAXa/QV3jZXGES7DdQlqPqqT3YjcMFLiRrWQR8cl4h" \
            "JIBRpV5piGyLmMMKYrWu7hQSrdRAEL3K6mNZZU6/yoG879LjtQbVwaFGPeT29B4zBE97FIo="

SIGNATURE2 = "Xla/AlirMihx72hehGMgpKILRUA2ZkEhFgVc65sl80iN+F62yQdSikGyUQVL+LaGNUgmzgK0zEahamfaMFep/9HE2FWuXlTCM+ZXx" \
             "OhGWUnjkGW9vi41/Turm7ALzaJoFm1f3Iv4nh1sRD1jySzlZvYwrq4LwmgZ8r0M+Q6xUSIIJfgS8Zjmp43strKo28vKT+DmUKu9Fg" \
             "jZWjW3S8WPPJFO0UqA0b1UQspmNLZOVxsNpa0OCM1pofJvT09n6xG+byV30Bed27Kw+D3fzfYq5xvohyeCyliTq8LHnOykecki3Y2" \
             "Pvl1qsxxBehlwc/WH8yIUiwC2Du6zY61tN3LGgMAoIFl40Roo1z/I7YfOy4ZCukOGqqyiLdjoXxIVQqqsPtKsrVXS+A9OQ+sVESgw" \
             "f8jeEIw/KXLVB/aEyrZJXQR1pBfqkOTCSnAfZVBSjJyxhanS/8iGmnRV5zz3auYMLR9aA8QHjV/VZOj0Bxhuba9VIzJlY9XoUt5Vs" \
             "h3uILJM3uVJzSjlZV+Jw3O+NdQFnZyh7m1+eJUMQJ8i0Sr3sMLsdb9me/I0HueXCa5eBHAoTtAyQgS4uN4NMhvpqrB/lQCx7pqnkt" \
             "xiCO/bUEZONQjWrvJT+EfD+I0UMFtPFiGDzJ0yi0Ah7LxSTGEGPFZHH5RgsJA8lJwGMCUtc9Cpy8A="

SIGNATURE3 = "hVdLwsWXe6yVy88m9H1903+Bj/DjSGsYL+ZIpEz+G6u/aVx6QfsvnWHzasjqN8SU+brHfL0c8KrapWcACO+jyCuXlHMZb9zKmJkHR" \
             "FSOiprCJ3tqNpv/4MIa9CXu0YDqnLHBSyxS01luKw3EqgpWPQdYcqDpOkjjTOq45dQC0PGHA/DXjP7LBptV9AwW200LIcL5Li8tDU" \
             "a8VSQybspDDfDpXU3+Xl5tJIBVS4ercPczp5B39Cwne4q2gyj/Y5RdIoX5RMqmFhfucw1he38T1oRC9AHTJqj4CBcDt7gc6jPHuzk" \
             "N7u1eUf0IK3+KTDKsCkkoHcGaoxT+NeWcS8Ki1A=="

XML = "<comment><guid>0dd40d800db1013514416c626dd55703</guid><parent_guid>69ab2b83-aa69-4456-ad0a-dd669" \
      "7f54714</parent_guid><text>Woop Woop</text><diaspora_handle>jaywink@iliketoast.net</diaspora_handle></comment>"

XML2 = "<comment><guid>d728fe501584013514526c626dd55703</guid><parent_guid>d641bd35-8142-414e-a12d-f956cc2c1bb9" \
       "</parent_guid><text>What about the mystical problem with &#x1F44D; (pt2 with more logging)</text>" \
       "<diaspora_handle>jaywink@iliketoast.net</diaspora_handle></comment>"


def get_dummy_private_key():
    return RSA.importKey(PRIVATE_KEY)
