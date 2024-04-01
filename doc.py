
def create_word_document_with_article_and_images(url):
    document = Document()
    heading, article_content, _ = fetch_article_content_and_styles(url)

    latest_image_url = None
    
    # Insert heading into the document
    if heading:
        document.add_heading(heading, level=1)

    for content in article_content:
        if content.name == 'img':
            if 'data-src' in content.attrs:
                latest_image_url = content['data-src']
            elif 'src' in content.attrs:
                latest_image_url = content['src']
            else:
                latest_image_url = None  # Or handle the missing URL case appropriately
        elif content.name in ['p', 'ul', 'ol']:
            if latest_image_url:
                resized_image = fetch_and_resize_image(latest_image_url, 400)
                if resized_image:
                    insert_image_to_document(document, resized_image)
                latest_image_url = None
            
            insert_styled_text_to_document(document, content)

    if latest_image_url:
        resized_image = fetch_and_resize_image(latest_image_url, 400)
        if resized_image:
            insert_image_to_document(document, resized_image)

    document_path = 'article_with_images.docx'
    document.save(document_path)
    print(f"Document saved as {document_path}")

def apply_css_styles_to_header(document, heading, css_styles):
    # Example of parsing CSS styles and applying to header
    style_sheet = cssutils.parseString(css_styles)
    for rule in style_sheet:
        if rule.type == rule.STYLE_RULE and 'h1' in rule.selectorText:
            font_size = rule.style.getPropertyValue('font-size')
            font_family = rule.style.getPropertyValue('font-family')
            # Create header with styles
            heading_paragraph = document.add_heading(heading, level=1)
            run = heading_paragraph.runs[0]
            if font_size.endswith('px'):
                pt_size = Pt(float(font_size[:-2]) * 0.75)  # Rough conversion, adjust as needed
                run.font.size = pt_size
            if font_family:
                run.font.name = font_family
            break
        