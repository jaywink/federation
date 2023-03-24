import copy
import json

from marshmallow import missing
from pyld import jsonld

from federation.entities.activitypub.constants import CONTEXT_ACTIVITYSTREAMS, CONTEXT_SECURITY, NAMESPACE_PUBLIC

# Extract context information from the metadata parameter defined for fields
# that are not part of the official AP spec. Use the same extended context for
# inbound payload. For outbound payload, build a context with only the required
# extensions
class LdContextManager:
    _named = [CONTEXT_ACTIVITYSTREAMS, CONTEXT_SECURITY]
    _extensions = {}
    _merged = []
    _models = []

    def __init__(self, models):
        self._models = models
        for klass in models:
            self._extensions[klass] = {}
            ctx = getattr(klass, 'ctx', [])
            if ctx:
                self._extensions[klass].update({klass.__name__:ctx})
            for name, value in klass.schema().declared_fields.items():
                ctx = value.metadata.get('ctx') or []
                if ctx:
                    self._extensions[klass].update({name:ctx})
        merged = {}
        for field in self._extensions.values():
            for ctx in field.values():
                self._add_extensions(ctx, self._named, merged)
        self._merged =  copy.copy(self._named)
        self._merged.append(merged)

    def _add_extensions(self, field, named, extensions):
        for item in field:
            if isinstance(item, str) and item not in named:
                named.append(item)
            elif isinstance(item, dict):
                extensions.update(item)


    def _get_fields(self, obj):
        for klass in self._extensions.keys():
            if issubclass(type(obj), klass):
                return self._extensions[klass]
        return {}

    def compact(self, obj):
        payload = jsonld.compact(obj.dump(), self.build_context(obj))
        patched = copy.copy(payload)

        # This is for platforms that don't handle the single element array
        # compaction to a single value and https://www.w3.org/ns/activitystreams#Public
        # being compacted to as:Public
        def patch_payload(payload, patched):
            for field in ('attachment', 'cc', 'tag', 'to'):
                value = payload.get(field)
                if value and not isinstance(value, list):
                    value = [value]
                    patched[field] = value
                if field in ('cc', 'to'):
                    try:
                        idx = value.index('as:Public')
                        patched[field][idx] = value[idx].replace('as:Public', NAMESPACE_PUBLIC)
                    except:
                        pass
            if isinstance(payload.get('object'), dict):
                patch_payload(payload['object'], patched['object'])

        patch_payload(payload, patched)
        return patched

    def build_context(self, obj):
        from federation.entities.activitypub.models import Object, Link

        final = [CONTEXT_ACTIVITYSTREAMS]
        extensions = {}

        def walk_object(obj):
            if type(obj) in self._extensions.keys():
                self._add_extensions(self._extensions[type(obj)].get(type(obj).__name__, []), final, extensions)
            to_add = self._get_fields(obj)
            for field in type(obj).schema().declared_fields.keys():
                field_value = getattr(obj, field)
                if field in to_add.keys():
                    if field_value is not missing or obj.signable and field == 'signature':
                        self._add_extensions(to_add[field], final, extensions)
                if not isinstance(field_value, list): field_value = [field_value]
                for value in field_value:
                    if issubclass(type(value), (Object, Link)):
                        walk_object(value)

        walk_object(obj)
        if extensions: final.append(extensions)
        # compact the array if len == 1 to minimize test changes
        return final if len(final) > 1 else final[0]

    def merge_context(self, ctx):
        # One platform sends a single string context
        if isinstance(ctx, str): ctx = [ctx]

        # add a # at the end of the python-federation string
        # for socialhome payloads
        s = json.dumps(ctx)
        if 'python-federation"' in s:
            ctx = json.loads(s.replace('python-federation', 'python-federation#', 1))

        # some platforms have http://joinmastodon.com/ns in @context. This
        # is not a json-ld document.
        try:
            ctx.pop(ctx.index('http://joinmastodon.org/ns'))
        except:
            pass

        # remove @language in context since this directive is not
        # processed by calamus. Pleroma adds a useless @language: 'und'
        # which is discouraged in best practices and in some cases makes
        # calamus return dict where str is expected.
        # see https://www.rfc-editor.org/rfc/rfc5646, page 56
        idx = []
        for i, v in enumerate(ctx):
            if isinstance(v, dict):
                v.pop('@language', None)
                if len(v) == 0: idx.insert(0, i)
        for i in idx: ctx.pop(i)

        # AP activities may be signed, but most platforms don't
        # define RsaSignature2017. add it to the context
        # hubzilla doesn't define the discoverable property in its context
        # include all Mastodon extensions for platforms that only define http://joinmastodon.org/ns in their context
        uris = []
        defs = {}
        # Merge original context dicts in one dict
        for item in ctx:
            if isinstance(item, str):
                uris.append(item)
            else:
                defs.update(item)

        for item in self._merged:
            if isinstance(item, str) and item not in uris:
                uris.append(item)
            elif isinstance(item, dict):
                defs.update(item)

        final = copy.copy(uris)
        final.append(defs)
        return final
