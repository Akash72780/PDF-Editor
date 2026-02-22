import fitz

class PDFEngine:
    def __init__(self):
        self.library = {}  # Stores filename: fitz.Document object

    def load_file(self, file_path):
        """Loads a single PDF into the library."""
        name = file_path.split("/")[-1]
        self.library[name] = fitz.open(file_path)
        return name

    def get_document(self, name):
        """Returns the specific document object."""
        return self.library.get(name)

    def merge_all(self):
        """Combines everything in the library into one new document."""
        if not self.library: return None
        merged_doc = fitz.open()
        for name in self.library:
            merged_doc.insert_pdf(self.library[name])
        return merged_doc

    def remove_file(self, name):
        """Removes a specific document from the library by name."""
        if name in self.library:
            self.library[name].close()
            del self.library[name]

    def delete_page(self, name, page_index):
        """Removes a specific page from a document in the library."""
        if name in self.library:
            doc = self.library[name]
            if 0 <= page_index < len(doc):
                doc.delete_page(page_index)
                return True
        return False

    def insert_at(self, target_name, source_name, position):
        """
        Inserts all pages of source_doc into target_doc after the 
        specified position (1-based index).
        """
        if target_name in self.library and source_name in self.library:
            target_doc = self.library[target_name]
            source_doc = self.library[source_name]
            
            # insert_pdf parameters: (source_doc, start_at=position)
            # Position 2 means it will start at index 2 (after page 1 and 2)
            target_doc.insert_pdf(source_doc, start_at=position)
            return True
        return False

    def clear(self):
        for doc in self.library.values():
            doc.close()
        self.library = {}

    def save_document(self, doc, output_path):
        """Saves a specific document object to a file."""
        if doc:
            doc.save(output_path)
            return True
        return False