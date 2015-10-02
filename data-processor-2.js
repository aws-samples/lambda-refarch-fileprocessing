/* Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use 
this file except in compliance with the License. A copy of the License is 
located at

http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or 
implied. See the License for the specific language governing permissions and 
limitations under the License. */

function getSNSMessageObject(msgString) {
    var x = msgString.replace(/\\/g, '');
    var y = x.substring(1, x.length - 1);
    var z = JSON.parse(y);
    return z;
}

exports.handler = function(event, context) {
    console.log('event: '+JSON.stringify(event));
    var snsMsgString = JSON.stringify(event.Records[0].Sns.Message);
    var snsMsgObject = getSNSMessageObject(snsMsgString);
    var srcBucket = snsMsgObject.Records[0].s3.bucket.name;
    var srcKey = snsMsgObject.Records[0].s3.object.key;
    console.log('SRC Bucket from data processor 2: ' + srcBucket);
    console.log('SRC Keyfrom data processor 2: ' + srcKey);

    context.succeed(null);
};
