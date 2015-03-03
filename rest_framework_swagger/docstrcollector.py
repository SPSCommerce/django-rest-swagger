from introspectors import APIViewIntrospector, APIViewMethodIntrospector
from docgenerator import DocumentationGenerator


def is_hidden_method(parser):
    return parser.object.get('hidden_method', False)


class DocstrMethodIntrospector(APIViewMethodIntrospector):

    def check_yaml_methods(self, yaml_methods):
        yaml_methods = (m for m in yaml_methods if m != 'api')
        return super(DocstrMethodIntrospector, self).check_yaml_methods(yaml_methods)


class DocstrIntrospector(APIViewIntrospector):

    def __iter__(self):
        for method_name in self.methods():
            method = DocstrMethodIntrospector(self, method_name)
            doc_parser = method.get_yaml_parser()
            if not is_hidden_method(doc_parser):
                yield method

    def get_api(self):
        parser = self.get_yaml_parser()
        return parser.object

    def get_models(self):
        model_classes = []
        if hasattr(self.callback, 'get_model_class'):
            root_model = self.callback.get_model_class()
            model_classes.append(root_model)
            model_classes.extend(
                self._get_releated_classes_models_list(root_model))
        return model_classes

    def _get_releated_classes_models_list(self, obj_class):
        releated_obj = []
        if hasattr(obj_class, "get_releated_models_classes"):
            releated_obj_classes = obj_class.get_releated_models_classes()
            releated_obj.extend(releated_obj_classes)
            for cls in releated_obj_classes:
                if hasattr(cls, "get_releated_models_classes"):
                    releated_obj.extend(
                        self._get_releated_classes_models_list(cls))
        return releated_obj


class DocstrCollector(DocumentationGenerator):

    def _get_method_serializer(self, method_introspector):
        pass

    def _get_method_response_type(
            self, doc_parser, serializer, introspector, method_introspector):
        return doc_parser.get_response_type()

    def get_models(self, apis):
        models = {}
        for api in apis:
            intro = self.get_introspector(api, apis)
            models_classes = intro.get_models()
            parser = intro.get_yaml_parser()
            for cls in models_classes:
                doc = parser.load_obj_from_docstring(cls.__doc__)
                models[cls.__name__] = doc

        return models

    def get_introspector(self, api, apis):
        callback = api['callback']
        path = api['path']
        pattern = api['pattern']
        return DocstrIntrospector(callback, path, pattern)
