import base64
import xml.etree.ElementTree as ET
import hashlib
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from typing import Tuple
from lxml import etree
from signxml import XMLSigner


class ZatcaEncoder:
    """محرك ترميز البيانات للامتثال لمتطلبات هيئة الزكاة والضريبة"""
    
    @staticmethod
    def _get_tlv_byte(tag: int, value: str) -> bytes:
        """تحويل الحقل إلى تنسيق Tag-Length-Value"""
        tag_buf = bytes([tag])
        val_buf = str(value).encode('utf-8')
        len_buf = bytes([len(val_buf)])
        return tag_buf + len_buf + val_buf

    @classmethod
    def generate_qr_base64(cls, seller: str, vat_no: str, timestamp: str, total: str, vat: str) -> str:
        """
        توليد الـ QR Code المطلوبة للمرحلة الأولى والثانية.
        الحقول: اسم المورد، الرقم الضريبي، الطابع الزمني، الإجمالي، مبلغ الضريبة.
        """
        tlv_data = (
            cls._get_tlv_byte(1, seller) +
            cls._get_tlv_byte(2, vat_no) +
            cls._get_tlv_byte(3, timestamp) +
            cls._get_tlv_byte(4, total) +
            cls._get_tlv_byte(5, vat)
        )
        return base64.b64encode(tlv_data).decode('utf-8')

    @classmethod
    def calculate_hash(cls, xml_content: str) -> str:
        """حساب بصمة SHA256 لملف XML المشفر بـ Base64"""
        digest = hashes.Hash(hashes.SHA256())
        digest.update(xml_content.encode('utf-8'))
        hash_bytes = digest.finalize()
        return base64.b64encode(hash_bytes).decode('utf-8')

    @classmethod
    def generate_ubl_xml(cls, invoice_data: dict) -> str:
        """إنشاء هيكل ملف XML (UBL 2.1) المتوافق مع المرحلة الثانية"""
        invoice = ET.Element("Invoice", {
            "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "xmlns:ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        })
        
        ET.SubElement(invoice, "cbc:ID").text = invoice_data['number']
        ET.SubElement(invoice, "cbc:UUID").text = invoice_data['uuid']
        ET.SubElement(invoice, "cbc:IssueDate").text = invoice_data['date']
        ET.SubElement(invoice, "cbc:IssueTime").text = invoice_data['time']
        
        # نوع الفاتورة (0100000 للفاتورة الضريبية، 0200000 للمبسطة)
        subtype = invoice_data.get('subtype', '388')
        ET.SubElement(invoice, "cbc:InvoiceTypeCode", {"name": invoice_data.get('type', '0200000')}).text = subtype

        # إضافة المرجع المالي للفاتورة الأصلية (مطلوب في الإشعارات 381 و 383)
        if subtype in ['381', '383'] and invoice_data.get('original_number'):
            billing_ref = ET.SubElement(invoice, "cac:BillingReference")
            inv_doc_ref = ET.SubElement(billing_ref, "cac:InvoiceDocumentReference")
            ET.SubElement(inv_doc_ref, "cbc:ID").text = invoice_data['original_number']
        
        # بيانات المورد
        supplier = ET.SubElement(invoice, "cac:AccountingSupplierParty")
        party = ET.SubElement(supplier, "cac:Party")
        ET.SubElement(ET.SubElement(party, "cac:PartyTaxScheme"), "cbc:CompanyID").text = invoice_data['supplier_vat']

        # بيانات المشتري (إلزامية في B2B)
        if invoice_data.get('buyer_name'):
            customer = ET.SubElement(invoice, "cac:AccountingCustomerParty")
            c_party = ET.SubElement(customer, "cac:Party")
            
            # العنوان البريدي للمشتري
            c_address = ET.SubElement(c_party, "cac:PostalAddress")
            ET.SubElement(c_address, "cbc:StreetName").text = invoice_data.get('buyer_street', 'NA')
            ET.SubElement(c_address, "cbc:BuildingNumber").text = invoice_data.get('buyer_building', 'NA')
            ET.SubElement(c_address, "cbc:CityName").text = invoice_data.get('buyer_city', 'NA')
            ET.SubElement(c_address, "cbc:PostalZone").text = invoice_data.get('buyer_postcode', 'NA')
            ET.SubElement(ET.SubElement(c_address, "cac:Country"), "cbc:IdentificationCode").text = "SA"

            if invoice_data.get('buyer_vat'):
                ET.SubElement(ET.SubElement(c_party, "cac:PartyTaxScheme"), "cbc:CompanyID").text = invoice_data['buyer_vat']
        
        # المبالغ والإجماليات
        monetary_total = ET.SubElement(invoice, "cac:LegalMonetaryTotal")
        ET.SubElement(monetary_total, "cbc:TaxExclusiveAmount", {"currencyID": "SAR"}).text = str(invoice_data['total_excl_vat'])
        ET.SubElement(monetary_total, "cbc:TaxInclusiveAmount", {"currencyID": "SAR"}).text = str(invoice_data['total_incl_vat'])
        ET.SubElement(monetary_total, "cbc:PayableAmount", {"currencyID": "SAR"}).text = str(invoice_data['total_incl_vat'])

        return ET.tostring(invoice, encoding='unicode')

    @classmethod
    def generate_csr(cls, company_name: str, vat_number: str, serial_number: str) -> Tuple[str, str]:
        """
        توليد طلب توقيع شهادة (CSR) ومفتاح خاص متوافق مع متطلبات ZATCA
        """
        # 1. توليد المفتاح الخاص (Private Key)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # 2. بناء بيانات الـ CSR حسب متطلبات الهيئة
        # ملاحظة: القيم مثل الـ OID (1.3.6.1.4.1.311.20.2) ضرورية للهيئة
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "SA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, company_name),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IT"),
            x509.NameAttribute(NameOID.COMMON_NAME, company_name),
        ])

        alt_names = x509.SubjectAlternativeName([
            x509.DirectoryName(x509.Name([
                x509.NameAttribute(x509.ObjectIdentifier("2.5.4.4"), serial_number), # Serial Number
                x509.NameAttribute(x509.ObjectIdentifier("2.5.4.15"), "Private"),    # Organization Category
                x509.NameAttribute(x509.ObjectIdentifier("2.5.4.11"), "Accounting"), # Unit
            ]))
        ])

        csr = x509.CertificateSigningRequestBuilder().subject_name(
            subject
        ).add_extension(
            alt_names, critical=False
        ).sign(private_key, hashes.SHA256())

        # 3. تحويل النتائج إلى نصوص PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode('utf-8')

        return csr_pem, private_key_pem

    @classmethod
    def sign_xml(cls, xml_content: str, private_key_pem: str, certificate_pem: str) -> str:
        """
        توقيع ملف XML رقمياً باستخدام المفتاح الخاص والشهادة.
        تستخدم مكتبة signxml لتسهيل عملية التوقيع بمعيار XMLDsig.
        """
        root = etree.fromstring(xml_content.encode('utf-8'))

        # يجب أن تتوافق الـ references مع ما تتوقعه ZATCA
        # عادة ما يتم توقيع كامل محتوى الفاتورة
        signer = XMLSigner(
            method=etree.QName("http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"),
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#" # Exclusive Canonicalization
        )
        
        # تحميل المفتاح الخاص والشهادة
        private_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
        certificate = x509.load_pem_x509_certificate(certificate_pem.encode('utf-8'))

        # توقيع الـ XML
        signed_root = signer.sign(root, key=private_key, cert=certificate)

        # تحويل الـ ElementTree إلى نص XML
        return etree.tostring(signed_root, pretty_print=True, encoding='unicode')