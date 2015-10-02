/* Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use 
this file except in compliance with the License. A copy of the License is 
located at

http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or 
implied. See the License for the specific language governing permissions and 
limitations under the License. */

/**
 * A Lambda function that sets the permissions for the specified SNS topic
 */
var aws = require("aws-sdk");

exports.handler = function(event, context) {

    console.log("REQUEST RECEIVED:\n" + JSON.stringify(event));

    // For Delete requests, immediately send a SUCCESS response.
    if (event.RequestType == "Delete") {
        sendResponse(event, context, "SUCCESS");
        return;
    }

    var responseStatus = "FAILED";
    var responseData = {};

    var lambda = new aws.Lambda({region: event.ResourceProperties.Region});
    var addPermissionParams = {
        Action: 'lambda:InvokeFunction',
        FunctionName: event.ResourceProperties.LambdaFx,
        Principal: 'sns.amazonaws.com',
        StatementId: 'stmt-id-101',
    };

    // Get AMI IDs with the specified name pattern and owner
    lambda.addPermission(addPermissionParams, function(err, addPermissionResult) {
        if (err) {
            responseData = {Error: "Add Permission call failed"};
            console.log(responseData.Error + ":\n", err);
        } else {
            responseStatus = "SUCCESS";
            responseData = { "Result" : addPermissionResult };
        }
        sendResponse(event, context, responseStatus, responseData);
    });
};


// Send response to the pre-signed S3 URL
function sendResponse(event, context, responseStatus, responseData) {

    var responseBody = JSON.stringify({
        Status: responseStatus,
        Reason: "See the details in CloudWatch Log Stream: " + context.logStreamName,
        PhysicalResourceId: context.logStreamName,
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
        Data: responseData
    });

    console.log("RESPONSE BODY:\n", responseBody);

    var https = require("https");
    var url = require("url");

    var parsedUrl = url.parse(event.ResponseURL);
    var options = {
        hostname: parsedUrl.hostname,
        port: 443,
        path: parsedUrl.path,
        method: "PUT",
        headers: {
            "content-type": "",
            "content-length": responseBody.length
        }
    };

    console.log("SENDING RESPONSE...\n");

    var request = https.request(options, function(response) {
        console.log("STATUS: " + response.statusCode);
        console.log("HEADERS: " + JSON.stringify(response.headers));
        // Tell AWS Lambda that the function execution is done
        context.done();
    });

    request.on("error", function(error) {
        console.log("sendResponse Error:" + error);
        // Tell AWS Lambda that the function execution is done
        context.done();
    });

    // write data to request body
    request.write(responseBody);
    request.end();
}
