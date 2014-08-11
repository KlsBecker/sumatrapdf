#!/usr/bin/env python

"""
Generates a list of all exports from libmupdf.dll from the function lists
contained in the mupdf/include/* headers (only MuPDF and MuXPS are included)
and adds exports for the other libraries contained within libmupdf.dll but
used by SumatraPDF-no-MuPDF.exe (unarr, libdjvu, zlib, lzma, libwebp).
"""

import os, re, util2

def generateExports(header, exclude=[]):
	if os.path.isdir(header):
		return "\n".join([generateExports(os.path.join(header, file), exclude) for file in os.listdir(header)])
	
	data = open(header, "r").read()
	data = re.sub(r"(?sm)^#ifndef NDEBUG\s.*?^#endif", "", data, 0)
	data = re.sub(r"(?sm)^#ifdef ARCH_ARM\s.*?^#endif", "", data, 0)
	data = re.sub(r"(?sm)^#ifdef FITZ_DEBUG_LOCKING\s.*?^#endif", "", data, 0)
	data = data.replace(" FZ_NORETURN;", ";")
	functions = re.findall(r"(?sm)^\w+ (?:\w+ )?\*?(\w+)\(.*?\);", data)
	return "\n".join(["\t" + name for name in functions if name not in exclude])

def collectFunctions(file):
	data = open(file, "r").read()
	return re.findall(r"(?sm)^\w+(?: \*\n|\n| \*| )((?:fz_|pdf_|xps_)\w+)\(", data)

LIBMUPDF_DEF = """\
; This file is auto-generated by gen_libmupdf.def.py

LIBRARY libmupdf
EXPORTS

; Fitz exports

%(fitz_exports)s

; MuPDF exports

%(mupdf_exports)s

; MuXPS exports

%(muxps_exports)s

; unarr exports (required for ZipUtil, RarUtil)

%(unarr_exports)s

; djvu exports (required for DjVuEngine)

	ddjvu_anno_get_hyperlinks
	ddjvu_context_create
	ddjvu_context_release
	ddjvu_document_create_by_data
	ddjvu_document_create_by_filename_utf8
	ddjvu_document_get_fileinfo_imp
	ddjvu_document_get_filenum
	ddjvu_document_get_outline
	ddjvu_document_get_pageanno
	ddjvu_document_get_pageinfo_imp
	ddjvu_document_get_pagenum
	ddjvu_document_get_pagetext
	ddjvu_document_job
	ddjvu_format_create
	ddjvu_format_release
	ddjvu_format_set_row_order
	ddjvu_free
	ddjvu_job_release
	ddjvu_job_status
	ddjvu_message_peek
	ddjvu_message_pop
	ddjvu_message_wait
	ddjvu_miniexp_release
	ddjvu_page_create_by_pageno
	ddjvu_page_get_type
	ddjvu_page_job
	ddjvu_page_render
	ddjvu_page_set_rotation
	ddjvu_stream_close
	ddjvu_stream_write
	miniexp_caddr
	miniexp_cadr
	miniexp_cddr
	miniexp_stringp
	miniexp_symbol
	miniexp_to_str
	minilisp_finish

; zlib exports (required for ZipUtil, PsEngine, PdfCreator, LzmaSimpleArchive)

	crc32
	deflate
	deflateEnd
	deflateInit_
	deflateInit2_
	gzclose
	gzerror
	gzopen
	gzopen_w
	gzprintf
	gzread
	gzseek
	gztell
	inflate
	inflateEnd
	inflateInit_
	inflateInit2_

; lzma exports (required for LzmaSimpleArchive)

	LzmaDecode
	x86_Convert

; libwebp exports (required for WebpReader)

	WebPDecodeBGRAInto
	WebPGetInfo
"""

def main():
	util2.chdir_top()
	os.chdir("mupdf")
	
	# don't include/export doc_* functions, support for additional input/output formats and form support
	doc_exports = collectFunctions("source/fitz/document.c") + collectFunctions("source/fitz/document-all.c") + collectFunctions("source/fitz/document-no-run.c") + ["fz_get_annot_type"]
	more_formats = collectFunctions("source/fitz/svg-device.c") + collectFunctions("source/fitz/output-pcl.c") + collectFunctions("source/fitz/output-pwg.c")
	form_exports = collectFunctions("source/pdf/pdf-form.c") + collectFunctions("source/pdf/pdf-event.c") + collectFunctions("source/pdf/pdf-appearance.c") + collectFunctions("source/pdf/js/pdf-jsimp-cpp.c") + ["pdf_access_submit_event", "pdf_init_ui_pointer_event"]
	misc_exports = collectFunctions("source/fitz/stream-prog.c") + collectFunctions("source/fitz/test-device.c")
	sign_exports = ["pdf_crypt_buffer", "pdf_read_pfx", "pdf_sign_signature", "pdf_signer_designated_name", "pdf_free_designated_name"]
	
	fitz_exports = generateExports("include/mupdf/fitz", doc_exports + more_formats + misc_exports)
	mupdf_exports = generateExports("include/mupdf/pdf", form_exports + sign_exports + ["pdf_open_compressed_stream"])
	muxps_exports = generateExports("include/mupdf/xps.h", ["xps_parse_solid_color_brush", "xps_print_path"])
	unarr_exports = generateExports("../ext/unarr/unarr.h")
	
	list = LIBMUPDF_DEF % locals()
	open("../src/libmupdf.def", "wb").write(list.replace("\n", "\r\n"))

if __name__ == "__main__":
	main()
