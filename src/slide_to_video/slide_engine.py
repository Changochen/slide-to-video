import fitz  # PyMuPDF
from .utils import par_execute


class SlideEngine(object):
    def slide_to_images(self, slide_path: str, output_path: str):
        return self.pdf_to_images(slide_path, output_path)

    def pdf_to_images(self, pdf_path, output_dir, dpi=300):
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        pages = list(range(len(pdf_document)))
        image_paths = [f"{output_dir}/slide_{page_num+1}.png" for page_num in pages]
        dpis = [dpi] * len(pages)
        pdf_documents = [pdf_document] * len(pages)
        par_execute(self.extract_one_page, pdf_documents, pages, image_paths, dpis)
        # Close the document
        pdf_document.close()
        return image_paths

    def extract_one_page(self, pdf_document, page_num, output_path, dpi=300):
        # Get the page
        page = pdf_document.load_page(page_num)

        zoom = dpi / 72

        mat = fitz.Matrix(zoom, zoom)

        # Render the page to an image with the specified resolution
        pix = page.get_pixmap(matrix=mat)

        # Save the image
        pix.save(output_path)
