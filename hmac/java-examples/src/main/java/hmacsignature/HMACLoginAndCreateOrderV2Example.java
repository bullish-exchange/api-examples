package hmacsignature;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.hash.Hashing;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.IOException;
import java.math.BigInteger;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

import static com.google.common.hash.Hashing.hmacSha256;
import static java.time.Instant.now;

public class HMACLoginAndCreateOrderV2Example {

    private static final String BULLISH_HOST_NAME = "https://api.exchange.bullish.com";

    /// HMAC API Keys - Replace with your trading public and private key /////
    private static final String BULLISH_HMAC_PUBLIC_KEY = "HMAC-2f657a60-4b3c-4c3a-8e8f-106b137adf9e";

    private static final String BULLISH_HMAC_PRIVATE_KEY = "fffec788-89e8-491f-9bcf-e669d70cdade";

    private static final String LOGIN_API_PATH = "/trading-api/v1/users/hmac/login";

    public static void main(String[] args) throws Exception {
        final ObjectMapper objectMapper = new ObjectMapper()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        // Login and fetch an accountId
        final LoginResponse loginResponse = login(objectMapper);
        final String tradingAccount = fetchFirstTradingAccountId(loginResponse.getToken(), objectMapper);
        System.out.println("Using tradingAccountId: " + tradingAccount);

        BigInteger nano = currentNanoSecond();
        final String createOrderUrlPath = "/trading-api/v2/orders";

        final CreateOrderRequest createOrderRequest = CreateOrderRequest.builder()
                .symbol("BTCUSDC")
                .commandType("V3CreateOrder")
                .type("LIMIT")
                .side("BUY")
                .price("1.5000") // Demo only. This is not likely to fill
                .quantity("1.0")
                .timeInForce("GTC")
                .clientOrderId(nano.toString())
                .tradingAccountId(tradingAccount)
                .build();

        final String bodyString = objectMapper.writeValueAsString(createOrderRequest);

        // Construct and sign the Create Order Request
        final BigInteger nonce = BigInteger.valueOf(now().toEpochMilli());
        nano = currentNanoSecond();

        // Construct the signing payload
        final String payLoadToSign =
                nonce.toString()
                + nano.toString()
                + "POST"
                + createOrderUrlPath
                + bodyString;

        // Get the signature
        final String signature_for_order = getSignatureForOrder(payLoadToSign);

        // Send signature along, in the request
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + createOrderUrlPath))
                .POST(HttpRequest.BodyPublishers.ofString(bodyString))
                .header("Content-type", "application/json")
                .header("Authorization", "Bearer " + loginResponse.getToken())
                .header("BX-SIGNATURE", signature_for_order)
                .header("BX-NONCE", nano.toString())
                .header("BX-TIMESTAMP", nonce.toString())
                .build();

        var response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            System.err.println(response.statusCode());
            System.err.println(response.body());
            throw new RuntimeException(response.body());
        }
        System.out.println("CreateOrder API response:");
        System.out.println(response.statusCode());
        System.out.println(response.body());
    }

    private static BigInteger currentNanoSecond() {
        final Instant now = now();
        return BigInteger.valueOf(now().toEpochMilli()).multiply(BigInteger.valueOf(1000)).add(BigInteger.valueOf(now.getNano()));
    }

    private static LoginResponse login(ObjectMapper objectMapper) throws Exception {

        // Construct and sign the Create Order Request
        final BigInteger nonce = BigInteger.valueOf(now().getEpochSecond());
        final BigInteger timestamp = BigInteger.valueOf(now().getEpochSecond()).multiply(BigInteger.valueOf(1000));

        final String messageToSign = timestamp.toString() + nonce.toString() + "GET" + LOGIN_API_PATH;
        final String signature_base64 = getSignature(messageToSign);

        // Do the login
        final HttpClient client = HttpClient.newHttpClient();
        final HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + LOGIN_API_PATH))
                .GET()
                .header("Content-type", "application/json")
                .header("BX-NONCE", nonce.toString())
                .header("BX-PUBLIC-KEY", BULLISH_HMAC_PUBLIC_KEY)
                .header("BX-SIGNATURE", signature_base64)
                .header("BX-TIMESTAMP", timestamp.toString())
                .build();
        final var response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            System.err.println();
            throw new RuntimeException("Unable to login");
        }
        System.out.println("Getting JWT token [Success]");
        return objectMapper.readValue(response.body(), LoginResponse.class);
    }

    public static String fetchFirstTradingAccountId(String jwtToken, ObjectMapper objectMapper) throws IOException, InterruptedException {
        final HttpClient client = HttpClient.newHttpClient();
        final HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BULLISH_HOST_NAME + "/trading-api/v1/accounts/trading-accounts"))
                .header("Content-type", "application/json")
                .header("Authorization", "Bearer " + jwtToken)
                .GET()
                .build();
        var response  = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw new RuntimeException("Unable to fetch accounts");
        }

        final Account[] accounts = objectMapper.readValue(response.body(), Account[].class);
        if (accounts != null && accounts.length > 0) {
            return accounts[0].tradingAccountId;
        }

        throw new RuntimeException("No trading accounts to fetch");
    }

    private static String getSignature(String toSign) throws Exception {
        return hmacSha256(BULLISH_HMAC_PRIVATE_KEY.getBytes(StandardCharsets.UTF_8))
                .hashString(toSign, StandardCharsets.UTF_8)
                .toString();
    }

    private static String getSignatureForOrder(String toSign) throws Exception {
        final String digest = Hashing.sha256().hashString(toSign, StandardCharsets.UTF_8).toString();
        return hmacSha256(BULLISH_HMAC_PRIVATE_KEY.getBytes(StandardCharsets.UTF_8)).hashString(digest, StandardCharsets.UTF_8).toString();
    }


    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    public static class LoginRequest {
        private String userId;
        private Long nonce;
        private Long expirationTime;
        private Boolean biometricsUsed;
        private String sessionKey;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    public static class LoginPayload {
        private String publicKey;
        private String signature;
        private LoginRequest loginPayload;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    public static class LoginResponse {
        private String authorizer;
        private String ownerAuthorizer;
        private String token;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    public static class Account {
        String tradingAccountId;
    }

    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Data
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class CreateOrderRequest {
        private String clientOrderId;
        private String commandType;
        private String price;
        private String quantity;
        private String side;
        private String symbol;
        private String timeInForce;
        private String tradingAccountId;
        private String type;
    }
}
