#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2014 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

import evcommon
import formatutil
import election
import exception_msg

REASON_MISSING = 0
REASON_UNKNOWN = 1
REASON_NO_VALIDATOR = 2
REASON_NOT_SINGLE_VALUE = 3
REASON_NOT_VALID = 4
REASON_NOT_ZIP = 5
REASON_MISSING_ELEMENTS = 6
REASON_TOO_MANY_ELEMENTS = 7
REASON_NO_BALLOT = 8
REASON_ZIPBOMB = 9
REASON_BAD_SIGNATURE = 10

REASONS = {
        REASON_MISSING : "missing",
        REASON_UNKNOWN : "unknown",
        REASON_NO_VALIDATOR : "validator missing",
        REASON_NOT_SINGLE_VALUE : "multiple values",
        REASON_NOT_VALID : "invalid",
        REASON_NOT_ZIP : "badzip",
        REASON_MISSING_ELEMENTS : "missing elements",
        REASON_TOO_MANY_ELEMENTS : "too many elements",
        REASON_NO_BALLOT : "no ballot",
        REASON_ZIPBOMB : "zipbomb",
        REASON_BAD_SIGNATURE : "bad signature",
}

VALIDATORS = {
    evcommon.POST_EVOTE : formatutil.is_vote,
    evcommon.POST_PERSONAL_CODE: formatutil.is_isikukood,
    evcommon.POST_VOTERS_FILES_SHA256: formatutil.is_voters_file_sha256,
    evcommon.POST_SESS_ID: formatutil.is_session_id,
    evcommon.POST_PHONENO: formatutil.is_mobid_phoneno,
    evcommon.POST_MID_POLL: formatutil.is_mobid_poll
}

def is_bdoc_mimetype_file(zi):
    size = len("application/vnd.etsi.asic-e+zip")
    fn = (zi.filename == 'mimetype')
    fs = (zi.file_size == size)
    cs = (zi.compress_size == size)
    return (fn and fs and cs)


def is_bdoc_metainf_dir(zi):
    fn = (zi.filename == 'META-INF/')
    fs = (zi.file_size == 0)
    cs = (zi.compress_size == 0)
    return (fn and fs and cs)


def is_bdoc_manifest_file(zi):
    fn = (zi.filename == 'META-INF/manifest.xml')
    fs = (zi.file_size < 1024)
    cs = (zi.compress_size < 1024)
    return (fn and fs and cs)


def is_encrypted_vote(zi):
    fs = (zi.file_size == 256)
    cs = (zi.compress_size == 256)
    return (fs and cs)


def is_bdoc_signature_file(zi):
    fn = (zi.filename == 'META-INF/signatures0.xml')
    fs = (zi.file_size < 5500)
    cs = (zi.compress_size < 5500)
    return (fn and fs and cs)


ZIPFILE_VALIDATORS = {
    'mimetype' : is_bdoc_mimetype_file,
    'META-INF/' : is_bdoc_metainf_dir,
    'META-INF/manifest.xml' : is_bdoc_manifest_file,
    'META-INF/signatures0.xml' : is_bdoc_signature_file
}


def get_invalid_keys(form, required):
    invalid = []

    for key in required:
        if not form.has_key(key):
            invalid.append((key, REASON_MISSING))

    for key in form:

        values = form.getlist(key)
        extra = "%d, %s" % (len(values), values[:200])

        if not key in required:
            invalid.append((key, REASON_UNKNOWN, extra))
            continue

        if not VALIDATORS.has_key(key):
            invalid.append((key, REASON_NO_VALIDATOR, extra))
            continue

        if len(values) > 1:
            invalid.append((key, REASON_NOT_SINGLE_VALUE, extra))
            continue

        if not VALIDATORS[key](values[0]):
            invalid.append((key, REASON_NOT_VALID, extra))
            continue

    return invalid


HDR_1 = \
"""<asic:XAdESSignatures xmlns:asic="http://uri.etsi.org/02918/v1.2.1#" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
<ds:Signature Id="S0">
<ds:SignedInfo xmlns:asic="http://uri.etsi.org/02918/v1.2.1#" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Id="S0-SignedInfo">
<ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11">
</ds:CanonicalizationMethod>
<ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha224">
</ds:SignatureMethod>
"""

HDR_2 = \
"""</ds:X509Data></ds:KeyInfo>
<ds:Object Id="S0-object-xades"><xades:QualifyingProperties Id="S0-QualifyingProperties" Target="#S0"><xades:SignedProperties xmlns:asic="http://uri.etsi.org/02918/v1.2.1#" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Id="S0-SignedProperties">
<xades:SignedSignatureProperties Id="S0-SignedSignatureProperties">
"""

HDR_3 = \
"""<xades:SigningCertificate>
<xades:Cert>
<xades:CertDigest>
<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#sha224">
</ds:DigestMethod>
"""

HDR_4 = \
"""</xades:IssuerSerial>
</xades:Cert>
</xades:SigningCertificate>
<xades:SignaturePolicyIdentifier>
<xades:SignaturePolicyId>
<xades:SigPolicyId>
<xades:Identifier Qualifier="OIDAsURN">
urn:oid:1.3.6.1.4.1.10015.1000.3.2.1</xades:Identifier>
</xades:SigPolicyId>
<xades:SigPolicyHash>
<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256">
</ds:DigestMethod>
<ds:DigestValue>3Tl1oILSvOAWomdI9VeWV6IA/32eSXRUri9kPEz1IVs=</ds:DigestValue>
</xades:SigPolicyHash>
<xades:SigPolicyQualifiers>
<xades:SigPolicyQualifier>
<xades:SPURI>
https://www.sk.ee/repository/bdoc-spec21.pdf</xades:SPURI>
</xades:SigPolicyQualifier>
</xades:SigPolicyQualifiers>
</xades:SignaturePolicyId>
</xades:SignaturePolicyIdentifier>
</xades:SignedSignatureProperties>
<xades:SignedDataObjectProperties>
"""

HDR_5 = \
"""
<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#sha224">
</ds:DigestMethod>
"""

HDR_6 = \
"""</xades:SignedDataObjectProperties>
</xades:SignedProperties>
<xades:UnsignedProperties></xades:UnsignedProperties></xades:QualifyingProperties></ds:Object>
</ds:Signature>
</asic:XAdESSignatures>
"""


def check_prefix(inp, prefix):
    if inp.startswith(prefix):
        return len(prefix)
    return -1


def check_tag(inp, tag_start, tag_end, is_good):
    if not inp.startswith(tag_start):
        return -1

    end = inp.find(tag_end)
    if end == -1:
        return -1

    start = len(tag_start)
    if is_good(inp[start:end]):
        return end + len(tag_end)

    return -1


def check_dataobjects(inp, questions):
    start = 0
    lines = []
    ii = 0
    for el in questions:
        lines.append(\
                "<xades:DataObjectFormat ObjectReference=\"#S0-ref-%d\">\n" % ii)
        lines.append(\
                "<xades:MimeType>application/octet-stream</xades:MimeType>\n")
        lines.append("</xades:DataObjectFormat>\n")
        ii += 1

    for line in lines:
        ret = check_prefix(inp[start:], line)
        if ret == -1:
            return -1
        start = start + ret

    return start


def check_references(inp, questions):
    start = 0
    ref_count = 0
    common_start = "<ds:Reference"
    tag_end = "</ds:Reference>\n"
    taglist = []
    taglist.append(\
            "<ds:Reference Id=\"S0-ref-sp\" Type=\"http://uri.etsi.org/01903#SignedProperties\" URI=\"#S0-SignedProperties\">")
    ii = 0
    for el in questions:
        taglist.append("<ds:Reference Id=\"S0-ref-%d\" URI=\"/%s.evote\">" % (ii, el))
        ii += 1

    while inp[start:].startswith(common_start):
        for tag_start in taglist:
            ret = check_prefix(inp[start:], tag_start)
            if ret > -1:
                taglist.remove(tag_start)
                break
        if ret == -1:
            return -1
        start = start + ret

        ret = check_prefix(inp[start:], HDR_5)
        if ret == -1:
            return -1
        start = start + ret

        ret = check_tag(inp[start:], "<ds:DigestValue>", \
                "</ds:DigestValue>\n</ds:Reference>\n", formatutil.is_base64)
        if ret == -1:
            return -1
        start = start + ret

        ref_count = ref_count + 1

    if ref_count < 2:
        return -1

    return start

def is_well_formed_id_signature(sigdata, questions):

    tag_s_sigval = "</ds:SignedInfo><ds:SignatureValue Id=\"S0-SIG\">\n"
    tag_e_sigval = "</ds:SignatureValue>\n<ds:KeyInfo Id=\"S0-KeyInfo\">\n"
    tag_s_x509 = "<ds:X509Data><ds:X509Certificate>"
    tag_e_x509 = "</ds:X509Certificate>"
    tag_s_stime = "<xades:SigningTime>"
    tag_e_stime = "</xades:SigningTime>\n"
    tag_s_digval = "<ds:DigestValue>"
    tag_e_digval = "</ds:DigestValue>\n"
    tag_s_issuer = "</xades:CertDigest>\n<xades:IssuerSerial>\n" + \
            "<ds:X509IssuerName>"
    tag_e_issuer = "</ds:X509IssuerName>\n"
    tag_s_serial = "<ds:X509SerialNumber>"
    tag_e_serial = "</ds:X509SerialNumber>\n"

    item1 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_1
                }
            }
    item2 = {
            'validator' : check_references,
            'arguments' : {
                'questions' : questions
                }
            }
    item3 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_sigval,
                'tag_end' : tag_e_sigval,
                'is_good' : formatutil.is_base64_lines
                }
            }
    item4 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_x509,
                'tag_end' : tag_e_x509,
                'is_good' : formatutil.is_base64_lines
                }
            }
    item5 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_2
                }
            }
    item6 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_stime,
                'tag_end' : tag_e_stime,
                'is_good' : formatutil.is_signing_time
                }
            }
    item7 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_3
                }
            }
    item8 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_digval,
                'tag_end' : tag_e_digval,
                'is_good' : formatutil.is_base64
                }
            }
    item9 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_issuer,
                'tag_end' : tag_e_issuer,
                'is_good' : formatutil.is_100utf8
                }
            }
    item10 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_serial,
                'tag_end' : tag_e_serial,
                'is_good' : formatutil.is_number100
                }
            }
    item11 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_4
                }
            }

    item12 = {
            'validator' : check_dataobjects,
            'arguments' : {
                'questions' : questions
                }
            }

    item13 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_6
                }
            }


    stream = []
    stream.append(item1)
    stream.append(item2)
    stream.append(item3)
    stream.append(item4)
    stream.append(item5)
    stream.append(item6)
    stream.append(item7)
    stream.append(item8)
    stream.append(item9)
    stream.append(item10)
    stream.append(item11)
    stream.append(item12)
    stream.append(item13)

    start = 0
    for item in stream:
        validator = item['validator']
        ret = validator(sigdata[start:], **item['arguments'])
        if ret == -1:
            return False, sigdata[start:start+200]
        start = start + ret

    if start == len(sigdata):
        return True, ''

    return False, sigdata[start:start+200]


def is_well_formed_signature(sigfile, questions):

    hdr1 = sigfile.readline()
    if hdr1 == "<Signature/>":
        hdr2 = sigfile.readline()
        if hdr2 == "":
            return True, ''

    if hdr1 == "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n":
        return is_well_formed_id_signature(sigfile.read(), questions)

    return False, hdr1


def is_well_formed_vote_file(votefile, questions):

    import zipfile

    zipf = zipfile.ZipFile(votefile, "r")
    ziplist = zipf.infolist()

    if (len(ziplist) <= len(ZIPFILE_VALIDATORS)):
        return False, ('vote', REASON_MISSING_ELEMENTS)

    question_validators = {}
    for el in questions:
        question_validators["%s.evote" % el] = is_encrypted_vote

    if (len(ziplist) > ((len(ZIPFILE_VALIDATORS) + len(question_validators)))):
        return False, ('vote', REASON_TOO_MANY_ELEMENTS)

    real_questions = []
    for el in ziplist:
        if ZIPFILE_VALIDATORS.has_key(el.filename):
            if not ZIPFILE_VALIDATORS[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)

            data = zipf.open(el.filename).read(el.file_size + 1)
            if len(data) > el.file_size:
                return False, (el.filename, REASON_ZIPBOMB)

            continue

        if question_validators.has_key(el.filename):
            if not question_validators[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)
            real_questions.append(el.filename.split('.')[0])
            continue

        return False, (el.filename, REASON_UNKNOWN)

    if len(real_questions) == 0:
        return False, ('vote', REASON_NO_BALLOT)

    if zipf.testzip() != None:
        return False, ('vote', REASON_NOT_ZIP)

    res, extra = is_well_formed_signature(\
            zipf.open('META-INF/signatures0.xml'), real_questions)

    if not res:
        return False, ('vote', REASON_BAD_SIGNATURE, extra)

    return True, ()


def is_well_formed_vote(b64, questions):

    if not formatutil.is_vote(b64):
        return False, ('vote', REASON_NOT_VALID)

    import StringIO
    import base64

    votedata = base64.b64decode(b64)
    votefile = StringIO.StringIO(votedata)
    return is_well_formed_vote_file(votefile, questions)


def validate_vote(vote, questions):
    try:
        logline = ''
        res, why = is_well_formed_vote(vote, questions)
        if res:
            return True, logline

        if len(why) == 2:
            logline = 'Invalid vote: key - %s, reason - %s' % \
                    (why[0], REASONS[why[1]])
        elif len(why) == 3:
            logline = 'Invalid vote: key - %s, reason - %s, extra - %s' % \
                    (why[0], REASONS[why[1]], why[2][:200])
        else:
            logline = 'Invalid vote: internal error'

        return False, logline
    except:
        logline = 'Invalid vote: key - exception, reason - %s' % \
                exception_msg.trace()
        return False, logline


def validate_form(form, required):
    try:
        logline = ''
        invalid = get_invalid_keys(form, required)
        if len(invalid) <> 0:
            logline = 'Invalid form: '
            for el in invalid:
                if len(el) == 2:
                    logline = "%skey - %s, reason - %s;" % \
                            (logline, el[0], REASONS[el[1]])
                elif len(el) == 3:
                    logline = "%skey - %s, reason - %s, extra - %s" % \
                            (logline, el[0], REASONS[el[1]], el[2][:200])
                else:
                    logline = "%sinternal error" % logline
            return False, logline

        if evcommon.POST_EVOTE in required:
            return validate_vote(\
                    form.getvalue(evcommon.POST_EVOTE), \
                    election.Election().get_questions())

        return True, logline
    except:
        logline = 'Invalid form: key - exception, reason - %s' % \
                exception_msg.trace()
        return False, logline


def validate_sessionid(form):

    key = evcommon.POST_SESS_ID

    if not form.has_key(key):
        return False

    if not VALIDATORS.has_key(key):
        return False

    values = form.getlist(key)
    if len(values) > 1:
        return False

    if not VALIDATORS[key](values[0]):
        return False

    return True


if __name__ == '__main__':
    pass
#    print is_well_formed_vote_file(open('debug_vote.bdoc'), ['RH2018', 'EP2018'])

