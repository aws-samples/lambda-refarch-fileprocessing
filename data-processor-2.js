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
