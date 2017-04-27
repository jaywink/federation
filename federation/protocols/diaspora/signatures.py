"""
Example Comment payload
-----------------------

<XML>  
    <post>    
        <comment>
            <guid>0dd40d800db1013514416c626dd55703</guid>      
            <parent_guid>69ab2b83-aa69-4456-ad0a-dd6697f54714</parent_guid>      
            <text>Woop Woop</text>
            <diaspora_handle>jaywink@iliketoast.net</diaspora_handle>
            <author_signature>A/vVRxM3V1ceEH1JrnPOaIZGM3gMjw/fnT9TgUh3poI4q9eH95AIoig+3eTA8XFuGvuo0tivxci4e0NJ1VLVkl/aqp8rvBNrRI1RQkn2WVF6zk15Gq6KSia/wyzyiJHGxNGM8oFY4qPfNp6K+8ydUti22J11tVBEvQn+7FPAoloF2Xz1waK48ZZCFs8Rxzj+4jlz1PmuXCnTj7v7GYS1Rb6sdFz4nBSuVk5X8tGOSXIRYxPgmtsDRMRrvDeEK+v3OY6VnT8dLTckS0qCwTRUULub1CGwkz/2mReZk/M1W4EbUnugF5ptslmFqYDYJZM8PA/g89EKVpkx2gaFbsC4KXocWnxHNiue18rrFQ5hMnDuDRiRybLnQkxXbE/HDuLdnognt2S5wRshPoZmhe95v3qq/5nH/GX1D7VmxEEIG9fX+XX+Vh9kzO9bLbwoJZwm50zXxCvrLlye/2JU5Vd2Hbm4aMuAyRAZiLS/EQcBlsts4DaFu4txe60HbXSh6nqNofGkusuzZnCd0VObOpXizrI8xNQzZpjJEB5QqE2gbCC2YZNdOS0eBGXw42dAXa/QV3jZXGES7DdQlqPqqT3YjcMFLiRrWQR8cl4hJIBRpV5piGyLmMMKYrWu7hQSrdRAEL3K6mNZZU6/yoG879LjtQbVwaFGPeT29B4zBE97FIo=</author_signature>
            <parent_author_signature/>
        </comment>
    </post>
</XML>

TODO:
* Add method to verify author signature
* Add method to create author signature

https://diaspora.github.io/diaspora_federation/federation/relayable.html

parent_author_signature part can be skipped as per discussion with Diaspora protcol team.
"""
