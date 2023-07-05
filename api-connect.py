from web3 import Web3
from flask import Flask, jsonify, request, render_template
import json
import flask
from config import PRIVATE_KEY
from config import PRIVATE_KEY
from dotenv.main import load_dotenv
import os

load_dotenv()


# Global variables

endPoint = os.environ['ENDPOINT']
alchemy_http = "https://eth-goerli.g.alchemy.com/v2/" + endPoint
# infura_sepolia = "https://sepolia.infura.io/v3/383258b208d84f47bd09ea2643b80768"
web3 = Web3(Web3.HTTPProvider(alchemy_http))

with open('ABI-2.json') as f:
    abi = json.load(f)

with open('token_standard_abi.json') as tf:
    tokenABI = json.load(tf)

contract_address = "0xAC6C38E05D1e0f7FBB87938D4A7e82F4CB6807eF"

contract =  web3.eth.contract(address = contract_address, abi = abi)

# Flask endpoints for every smart contract functions
app = Flask(__name__)

@app.route("/", methods=['POST','GET'])
def home():
    contractAdmin = contract.functions.contractAdmin().call()
    return render_template('index.html', contractAdmin=contractAdmin)

@app.route('/contract-owner')
def owner():
    contractAdmin = contract.functions.contractAdmin().call()
    return f"Owner of this contract is {contractAdmin}"
    
@app.route('/token-balance')
def tokenBalance():
    args = request.args
    tokenAddress= args.get('token')
    userAddress = args.get('userAddress')
    #tokenAddress = "0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844"
    tokenContract = web3.eth.contract(address=tokenAddress, abi = tokenABI)
    tokenBal = tokenContract.functions.balanceOf(userAddress).call()
    return (f"Token Name : {tokenContract.functions.name().call()}\n"
            f"Token Symbol : {tokenContract.functions.symbol().call()}\n"
            f"Token Decimals : {tokenContract.functions.decimals().call()}\n"
            f"User Balance : {web3.fromWei(tokenBal, 'ether')}\n"
    )


@app.route('/user-balance')
def getUserBalance():
    args = request.args
    userAddress = args.get('address')
    userBalance = web3.eth.get_balance(userAddress)
    return f"User balance : {userBalance}"


@app.route('/send-transaction', methods=["POST"])
def sendRawTransaction():
    # 0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844 DAI
    # 
    received_data = request.get_json(force=True)
    senderAddress = received_data['senderAddress']
    senderPrivateKey = received_data['senderPrivateKey']
    receiverAddress = received_data['receiverAddress']
    value = web3.toWei(received_data['value'], 'ether')
    gas = 300000
    gasPrice = web3.toWei(received_data['gasPrice'], 'gwei')
    nonce = web3.eth.getTransactionCount(senderAddress)

    # create or build the transaction in form of dictionary
    transaction = {
        'nonce': nonce,
        'to' : receiverAddress,
        'value': value,
        'gas':gas,
        'gasPrice': gasPrice
    }

    # sign the transaction
    signedTransaction = web3.eth.account.sign_transaction(transaction, senderPrivateKey)

    # send the transaction and get the hash
    transaction_hash = web3.eth.send_raw_transaction(signedTransaction.rawTransaction)

    # get the transaction hash
    dictToReturn = {'tx_hash':web3.toHex(transaction_hash)}
    return dictToReturn


@app.route('/send-token', methods=["POST"])
def sendToken():
    

    received_data = request.get_json(force=True)
    senderAddress = received_data['senderAddress']
    senderPrivateKey = received_data['senderPrivateKey']
    receiverAddress = received_data['receiverAddress']
    tokenAddress = received_data['tokenAddress']
    
    gas = 300000
    gasPrice = web3.toWei(received_data['gasPrice'], 'gwei')
    nonce = web3.eth.getTransactionCount(senderAddress)

    # Token variables
    tokenContract = web3.eth.contract(address=tokenAddress, abi = tokenABI)
    # tokenSymbol = tokenContract.functions.symbol().call()
    tokenDecimals = tokenContract.functions.decimals().call()
    tokenName = tokenContract.functions.name().call()
    tokenBalanceOf = tokenContract.functions.balanceOf(senderAddress).call()
    
    value = received_data['value'] * 10 **tokenDecimals
    # create or build the transaction in form of dictionary
    transaction = tokenContract.functions.transfer(
        receiverAddress,
        value
    ).buildTransaction({
        'nonce': nonce,
        'gas':gas,
        'gasPrice': gasPrice
    })
        

    # sign the transaction
    signedTransaction = web3.eth.account.sign_transaction(transaction, senderPrivateKey)

    # send the transaction and get the hash
    transaction_hash = web3.eth.send_raw_transaction(signedTransaction.rawTransaction)

    # get the transaction hash
    dictToReturn = {'tx_hash':web3.toHex(transaction_hash),"tokenName":tokenName,"sender":senderAddress,"receiver": receiverAddress,"value":value}
    # dictToReturn = {"tokenName":tokenName,"sender":senderAddress,"receiver": receiverAddress,"value":value,"gasPrice":gasPrice,"balance":tokenBalanceOf}
    return dictToReturn

@app.route('/add', methods=['POST'])
def addition():
    received_data = request.get_json(force=True)
    nb1 = received_data['nb1']
    nb2 = received_data['nb2']
    sum = nb1 + nb2
    returnValue = {'nb1':nb1, 'nb2':nb2, 'sum':sum}
    return returnValue

if __name__ == "__main__":
    app.run(debug=True)