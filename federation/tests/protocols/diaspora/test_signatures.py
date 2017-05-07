from lxml import etree

from federation.protocols.diaspora.signatures import verify_relayable_signature, create_relayable_signature
from federation.tests.fixtures.keys import get_dummy_private_key

XML = "<comment><guid>0dd40d800db1013514416c626dd55703</guid><parent_guid>69ab2b83-aa69-4456-ad0a-dd669" \
      "7f54714</parent_guid><text>Woop Woop</text><diaspora_handle>jaywink@iliketoast.net</diaspora_handle></comment>"

XML2 = "<comment><guid>d728fe501584013514526c626dd55703</guid><parent_guid>d641bd35-8142-414e-a12d-f956cc2c1bb9" \
       "</parent_guid><text>What about the mystical problem with &#x1F44D; (pt2 with more logging)</text>" \
       "<diaspora_handle>jaywink@iliketoast.net</diaspora_handle></comment>"

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

PUBKEY = "-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAuCfU1G5X+3O6vPdSz6QY\nSFbgdbv3KPv" \
         "xHi8tRmlyOLdLt5i1eqsy2WCW1iYNijiCL7OfbrvymBQxe3GA9S64\nVuavwzQ8nO7nzpNMqxY5tBXsBM1lECCHDOvm5dzINXWT9Sg7P1" \
         "8iIxE/2wQEgMUL\nAeVbJtAriXM4zydL7c91agFMJu1aHp0lxzoH8I13xzUetGMutR1tbcfWvoQvPAoU\n89uAz5j/DFMhWrkVEKGeWt1" \
         "YtHMmJqpYqR6961GDlwRuUsOBsLgLLVohzlBsTBSn\n3580o2E6G3DEaX0Az9WB9ylhNeV/L/PP3c5htpEyoPZSy1pgtut6TRYQwC8wns" \
         "qO\nbVIbFBkrKoaRDyVCnpMuKdDNLZqOOfhzas+SWRAby6D8VsXpPi/DpeS9XkX0o/uH\nJ9N49GuYMSUGC8gKtaddD13pUqS/9rpSvLD" \
         "rrDQe5Lhuyusgd28wgEAPCTmM3pEt\nQnlxEeEmFMIn3OBLbEDw5TFE7iED0z7a4dAkqqz8KCGEt12e1Kz7ujuOVMxJxzk6\nNtwt40Sq" \
         "EOPcdsGHAA+hqzJnXUihXfmtmFkropaCxM2f+Ha0bOQdDDui5crcV3sX\njShmcqN6YqFzmoPK0XM9P1qC+lfL2Mz6bHC5p9M8/FtcM46" \
         "hCj1TF/tl8zaZxtHP\nOrMuFJy4j4yAsyVy3ddO69ECAwEAAQ==\n-----END PUBLIC KEY-----\n"


def test_verify_relayable_signature():
    doc = etree.XML(XML)
    assert verify_relayable_signature(PUBKEY, doc, SIGNATURE)


def test_verify_relayable_signature_with_unicode():
    doc = etree.XML(XML2)
    assert verify_relayable_signature(PUBKEY, doc, SIGNATURE2)


def test_create_relayable_signature():
    doc = etree.XML(XML)
    signature = create_relayable_signature(get_dummy_private_key(), doc)
    assert signature == SIGNATURE3
