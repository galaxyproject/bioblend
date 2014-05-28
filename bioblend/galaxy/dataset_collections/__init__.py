class HasElements(object):

    def __init__(self, name, type="list", elements=[]):
        self.name = name
        self.type = type
        if isinstance(elements, dict):
            self.elements = []
            for key, value in elements.itervalues():
                self.elements.append(dict(name=key, id=value, src="hda"))
        elif elements:
            self.elements = elements

    def add(self, element):
        self.elements.append(element)
        return self


class CollectionDescription(HasElements):

    def to_dict(self):
        return dict(
            name=self.name,
            collection_type=self.type,
            element_identifiers=map(lambda e: e.to_dict(), self.elements)
        )


class CollectionElement(HasElements):

    def to_dict(self):
        return dict(
            src="new_collection",
            name=self.name,
            collection_type=self.type,
            element_identifiers=map(lambda e: e.to_dict(), self.elements)
        )


class SimpleElement(object):

    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return self.value


class HistoryDatasetElement(SimpleElement):

    def __init__(self, name, id):
        super(HistoryDatasetElement, self).__init__(dict(
            name=name,
            src="hda",
            id=id,
        ))


class HistoryDatasetCollectionElement(SimpleElement):

    def __init__(self, name, id):
        super(HistoryDatasetCollectionElement, self).__init__(dict(
            name=name,
            src="hdca",
            id=id,
        ))


class LibraryDatasetElement(SimpleElement):

    def __init__(self, name, id):
        super(LibraryDatasetElement, self).__init__(dict(
            name=name,
            src="ldda",
            id=id,
        ))


__all__ = [
    "CollectionDescription",
    "CollectionElement",
    "HistoryDatasetElement",
    "HistoryDatasetCollectionElement",
    "LibraryDatasetElement",
]
