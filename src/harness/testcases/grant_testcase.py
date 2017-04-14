#    Copyright 2016 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# Some parts of this software was developed by employees of 
# the National Institute of Standards and Technology (NIST), 
# an agency of the Federal Government. 
# Pursuant to title 17 United States Code Section 105, works of NIST employees 
# are not subject to copyright protection in the United States and are 
# considered to be in the public domain. Permission to freely use, copy, 
# modify, and distribute this software and its documentation without fee 
# is hereby granted, provided that this notice and disclaimer of warranty 
# appears in all copies.

# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER 
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY
# THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM 
# INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE 
# SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT
# SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, 
# INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, 
# OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON 
# WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED
# BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED
# FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES 
# PROVIDED HEREUNDER.

# Distributions of NIST software should also include copyright and licensing 
# statements of any third-party software that are legally bundled with the 
# code in compliance with the conditions of those licenses.

import json
import os
import unittest

import sas
from util import winnforum_testcase


class GrantTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def _assert_valid_response_format_for_approved_grant(self, grant_response):
    """Validate an approved grant response.

    Check presense and basic validity of each required field.
    Check basic validity of optional fields if they exist.
    Args:
      grant_response: A dictionary with a single grant response object from an
        array originally returned by a SAS server as specified in TS

    Returns:
      Nothing. It asserts if something about the response is broken/not per
      specs. Assumes it is dealing with an approved request.
    """
    # Check required string fields
    for field_name in ('cbsdId', 'grantId', 'grantExpireTime', 'channelType'):
      self.assertTrue(field_name in grant_response)
      self.assertGreater(len(grant_response[field_name]), 0)

    self.assertTrue('heartbeatInterval' in grant_response)

    if 'measReportConfig' in grant_response:
      self.assertGreater(len(grant_response['measReportConfig']), 0)

    # operationParam should not be set if grant is approved
    self.assertFalse('operationParam' in grant_response)

    self.assertTrue(grant_response['channelType'] in ('PAL', 'GAA'))

  @winnforum_testcase
  def test_10_7_4_1_1_1_1(self):
    """Successful CBSD grant request.
    CBSD sends a single grant request when no incumbent is present in the GAA
    frequency range requested by the CBSD. Response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['grantId'])
    self.assertEqual(response['channelType'], 'GAA')
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_10_7_4_1_3_1_2_1(self):
    """CBSD grant request when CBSD ID does not exist in SAS.
    CBSD sends grant request when its CBSD Id is not in SAS. The response
    should be FAIL.
    """

    # Request grant before registration, thus the CBSD ID does not exist in SAS
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = 'A non-exist cbsd id'
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

 @winnforum_testcase
  def test_WINFF_FT_S_GRA_2(self):
    """Successful CBSD grant request.
    Incumbent is present in the GAA frequency range requested by the
    CBSD which is outside the protection zone..
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response
    # Create and trigger the ESC Zone
    esc_zone_not_contain_device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'esc_zone_not_contain_device_a.json')))
    zone_request= {'zone':esc_zone_not_contain_device_a}
    zone_response = self._sas_admin.InjectEscZone(zone_request)
    trigger_esc_zone_request = {'zone_id': zone_response['zone_id'],
                                    'frequency_range': {
                                     'lowFrequency': 3620000000.0,
                                     'highFrequency': 3630000000.0}}
    trigger_id = self._sas_admin.TriggerEscZone(trigger_esc_zone_request)
    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertTrue(response['grantId'])
    self.assertEqual(response['channelType'], 'GAA')
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_3(self):
    """Successful CBSD grant request.
    Federal Incumbent is present in the GAA frequency range requested by
    the CBSD which is inside the protection zone of Federal Incumbent.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    esc_zone_contains_device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'esc_zone_contains_device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response
    # Create and trigger the ESC Zone
    esc_zone_contains_device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'esc_zone_contains_device_a.json')))
    zone_request = {'zone':esc_zone_contains_device_a}
    zone_response = self._sas_admin.InjectEscZone(zone_request)
    trigger_esc_zone_request = {'zone_id': zone_response['zone_id'],
                                    'frequency_range': {
                                     'lowFrequency': 3620000000.0,
                                     'highFrequency': 3630000000.0}}
    trigger_id = self._sas_admin.TriggerEscZone(trigger_esc_zone_request)
    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    if(response['response']['responseCode']== 0) :
      self.assertTrue('grantId' in response)
      self.assertEqual(response['channelType'], 'GAA')
      grant_id = response['grantId']
      del request, response
      request = {
      'heartbeatRequest': [{'cbsdId': cbsd_id,'grantId': grant_id,'operationState': 'GRANTED'}]}
      response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
      # Check the heartbeat response
      self.assertEqual(response['cbsdId'], cbsd_id)
      self.assertEqual(response['grantId'], grant_id)
      self.assertFalse('transmitExpireTime' in response)
      self.assertEqual(response['response']['responseCode'], 501)
    else:
      self.assertFalse('grantId' in response)
      self.assertEqual(response['response']['responseCode'], 400)

  @winnforum_testcase 
  def test_WINFF_FT_S_GRA_7(self):
    """CBSD sends grant with missing cbsdId. The response should be
      responseCode = 102 or 105.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertFalse('cbsdId' in response)
    self.assertFalse('grantId' in response)
    self.assertTrue((response['response']['responseCode'] == 102) or \
                    (response['response']['responseCode'] == 105))
					
  @winnforum_testcase
  def test_WINFF_FT_S_GRA_8(self):
    """CBSD grant request with missing operationParams.

    The operationParams object is missing in the grant request. The response
    should be FAIL.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # operationParams object is NOT present in the grant request.
    grant_0 = {'cbsdId': cbsd_id}
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)
 
  @winnforum_testcase
  def test_WINFF_FT_S_GRA_9(self):
    """Missing maxEirp in operationParam object.
    The maxEirp parameter is missing in the grant request. The response
    should be FAIL.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['maxEirp']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)
	
  @winnforum_testcase
  def test_WINFF_FT_S_GRA_10(self):
    """Missing lowFrequency in operationParam object.
    The lowFrequency parameter is missing in the grant request. The response
    should be FAIL.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['operationFrequencyRange']['lowFrequency']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)
	
  @winnforum_testcase
  def test_WINFF_FT_S_GRA_11(self):
    """Missing highFrequency in operationParam object.
    The highFrequency parameter is missing in the grant request. The response
    should be FAIL.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grant
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    del grant_0['operationParam']['operationFrequencyRange']['highFrequency']
    request = {'grantRequest': [grant_0]}
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_14(self):
    """lowFrequency and highFrequency value in operationParam mutually invalid.
    The response should be 103 (INVALID_PARAM)
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with mutually invalid frequency range
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3630000000.0
    grant_0['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3620000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_16(self):
    """Frequency range is completely outside 3550-3700 MHz.
    The response should be 103 (INVALID_PARAM) or 300 (UNSUPPORTED_SPECTRUM)
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with frequency range outside 3550-3700 MHz
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3350000000.0
    grant_0['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3450000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 300))

  @winnforum_testcase
  def test_WINNF_FT_S_GRA_17(self):
    """Frequency range value in operationParam partially outside 3550-3700 MHz.
    The response should be 103 (INVALID_PARAM) or 300 (UNSUPPORTED_SPECTRUM)
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with frequency range partially outside 3550-3700 Mhz
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'][
        'lowFrequency'] = 3450000000.0
    grant_0['operationParam']['operationFrequencyRange'][
        'highFrequency'] = 3650000000.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (103, 300))

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_21(self):
    """maxEirp in Grant Request for Category A is unsupported.

    The response should be 202 (CATEGORY_ERROR)
    """
    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with maxEirp exceeding maximum allowable (which is
    # 30 dBm/10 MHz)
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['maxEirp'] = 31.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertEqual(response['response']['responseCode'], 202)

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_22(self):
    """maxEirp in Grant Request for Category B is unsupported.

    The response should be 202 (CATEGORY_ERROR) or 103 (INVALID_VALUE)
    """
    # Register the device
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Create Grant Request with maxEirp exceeding maximum allowable EIRP (which
    # is 47 dBm/10 MHz)
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['maxEirp'] = 48.0
    request = {'grantRequest': [grant_0]}
    # Send grant request and get response
    response = self._sas.Grant(request)['grantResponse'][0]
    # Check grant response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response)
    self.assertTrue(response['response']['responseCode'] in (202, 103))

  @winnforum_testcase
  def test_WINFF_FT_S_GRA_23(self):
    """Dual grant requests for two devices. Successful case.

    The response should be 0 (NO_ERROR)
    """
    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Create grant requests
    grant_0 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_0['cbsdId'] = cbsd_ids[0]
    grant_1['cbsdId'] = cbsd_ids[1]
    # Request for non-overlapping frequency spectrum
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3620000000.0,
        'highFrequency': 3630000000.0
    }
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3640000000.0,
        'highFrequency': 3650000000.0
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Send grant requests
    response = self._sas.Grant(request)['grantResponse']
    # Check grant response
    self.assertEqual(len(response), 2)
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertTrue('grantId' in resp)
      self._assert_valid_response_format_for_approved_grant(resp)
      self.assertEqual(resp['response']['responseCode'], 0)
