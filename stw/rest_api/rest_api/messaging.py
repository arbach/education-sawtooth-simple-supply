from sawtooth_sdk.protobuf import client_batch_submit_pb2
from sawtooth_rest_api.protobuf import client_state_pb2
from sawtooth_rest_api.protobuf import validator_pb2

from rest_api.errors import ApiBadRequest, ApiInternalError


async def send(conn, timeout, batches):
    batch_request = client_batch_submit_pb2.ClientBatchSubmitRequest()
    batch_request.batches.extend(batches)
    await conn.send(
        validator_pb2.Message.CLIENT_BATCH_SUBMIT_REQUEST,
        batch_request.SerializeToString(),
        timeout)


async def check_batch_status(conn, batch_ids):
    status_request = client_batch_submit_pb2.ClientBatchStatusRequest(
        batch_ids=batch_ids, wait=True)
    validator_response = await conn.send(
        validator_pb2.Message.CLIENT_BATCH_STATUS_REQUEST,
        status_request.SerializeToString())

    status_response = client_batch_submit_pb2.ClientBatchStatusResponse()
    status_response.ParseFromString(validator_response.content)
    batch_status = status_response.batch_statuses[0].status
    if batch_status == client_batch_submit_pb2.ClientBatchStatus.INVALID:
        invalid = status_response.batch_statuses[0].invalid_transactions[0]
        raise ApiBadRequest(invalid.message)
    elif batch_status == client_batch_submit_pb2.ClientBatchStatus.PENDING:
        raise ApiInternalError("Transaction submitted but timed out")
    elif batch_status == client_batch_submit_pb2.ClientBatchStatus.UNKNOWN:
        raise ApiInternalError("Something went wrong. Try again later")


async def get_state_by_address(conn, address_suffix):
    status_request = client_state_pb2.ClientStateListRequest(address=address_suffix)
    validator_response = await conn.send(
        validator_pb2.Message.CLIENT_STATE_LIST_REQUEST,
        status_request.SerializeToString())

    status_response = client_state_pb2.ClientStateListResponse()
    status_response.ParseFromString(validator_response.content)

    return status_response
