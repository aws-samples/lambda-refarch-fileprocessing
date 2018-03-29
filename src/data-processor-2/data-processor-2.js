/* Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use
this file except in compliance with the License. A copy of the License is
located at

http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing permissions and
limitations under the License. */

var AWS = require('aws-sdk');
var removeMD = require('remove-markdown');
var async = require('async');

var s3 = new AWS.S3();

function getSNSMessageObject(msgString) {
  var x = msgString.replace(/\\/g, '');
  var y = x.substring(1, x.length - 1);
  var z = JSON.parse(y);
  return z;
}

exports.handler = function (event, context) {
  console.log('event: ' + JSON.stringify(event));
  var snsMsgString = JSON.stringify(event.Records[0].Sns.Message);
  var snsMsgObject = getSNSMessageObject(snsMsgString);

  var obj = {
    'bucket': snsMsgObject.Records[0].s3.bucket.name,
    'bucketOut': String(snsMsgObject.Records[0].s3.bucket.name + "-out"),
    'key': snsMsgObject.Records[0].s3.object.key
  };

  async.waterfall([
    function download(next) {
      // get Markdown object
      s3.getObject(
        {
          Bucket: obj.bucket,
          Key: obj.key
        },
        next);
    },
    function transform(response, next) {
      // strip out md and convert to plaintext
      var data = removeMD(String(response.Body));
      next(null, data);
    },
    function upload(data, next) {
      // change file extension
      var newFileName = obj.key.split(".")[0] + ".txt";
      console.log("Uploading data to: " + obj.bucketOut);
      s3.putObject(
        {
          Bucket: obj.bucketOut,
          Key: newFileName,
          Body: data,
          ContentType: "text/plain" // set contentType as plaintext
        },
        next);
    }
  ], function (err) {
    if (err) {
      console.error(err);
    } else {
      console.log('Success');
    }
    context.done();
  });

};
