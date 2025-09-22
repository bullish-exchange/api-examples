/// <summary>
/// Bullish Exchange Order Creator - C# Implementation
/// 
/// This class handles JWT authentication and order creation for Bullish Exchange API.
/// Based on the Python example: https://github.com/bullish-exchange/api-examples/blob/master/orders/create_order_hmac.py
/// 
/// SETUP INSTRUCTIONS:
/// 1. Create new console project: dotnet new console -n BullishTest
/// 2. Add packages:
///    - dotnet add package Microsoft.Extensions.Hosting
///    - dotnet add package Microsoft.Extensions.Http  
///    - dotnet add package Microsoft.Extensions.Logging.Console
/// 3. Set environment variables with your credentials:
///    - BX_API_HOSTNAME (e.g., "https://api.simnext.bullish-test.com")
///    - BX_PUBLIC_KEY (your HMAC public key)
///    - BX_SECRET_KEY (your HMAC secret key)  
///    - BX_TRADING_ACCOUNT_ID (your trading account ID)
///    - BX_RATELIMIT_TOKEN (optional rate limit token)
/// 4. Register in DI container:
///    services.AddHttpClient<BullishOrderCreator>();
///    services.AddLogging(builder => builder.AddConsole());
/// 
///
/// Usage:
///   var orderCreator = serviceProvider.GetRequiredService<BullishOrderCreator>();
///   var result = await orderCreator.CreateOrderWithAutoJwtAsync();
/// </summary>

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace BullishExchange;

/// <summary>
/// Main class for Bullish Exchange API integration
/// Handles HMAC authentication and order creation
/// </summary>
public class BullishOrderCreator
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<BullishOrderCreator> _logger;
    private readonly string _hostName;
    private readonly string _publicKey;
    private readonly string _secretKey;
    private readonly string _tradingAccountId;
    private readonly string _rateLimitToken;

    /// <summary>
    /// Constructor - loads configuration from environment variables
    /// </summary>
    /// <param name="httpClient">Injected HttpClient for API calls</param>
    /// <param name="logger">Injected logger for debugging</param>
    public BullishOrderCreator(HttpClient httpClient, ILogger<BullishOrderCreator> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        
        // Load environment variables
        _hostName = Environment.GetEnvironmentVariable("BX_API_HOSTNAME") 
                   ?? throw new InvalidOperationException("BX_API_HOSTNAME environment variable is required");
        _publicKey = Environment.GetEnvironmentVariable("BX_PUBLIC_KEY") 
                    ?? throw new InvalidOperationException("BX_PUBLIC_KEY environment variable is required");
        _secretKey = Environment.GetEnvironmentVariable("BX_SECRET_KEY") 
                    ?? throw new InvalidOperationException("BX_SECRET_KEY environment variable is required");
        _tradingAccountId = Environment.GetEnvironmentVariable("BX_TRADING_ACCOUNT_ID") 
                           ?? throw new InvalidOperationException("BX_TRADING_ACCOUNT_ID environment variable is required");
        _rateLimitToken = Environment.GetEnvironmentVariable("BX_RATELIMIT_TOKEN"); // Optional
    }

    /// <summary>
    /// Generate JWT token for API authentication
    /// Step 1 of the authentication process
    /// </summary>
    /// <returns>JWT token string for subsequent API calls</returns>
    public async Task<string> GenerateJwtTokenAsync()
    {
        try
        {
            // CRITICAL: Use correct timestamp formats
            var utcNow = DateTime.UtcNow;
            var nonce = (long)(utcNow - DateTime.UnixEpoch).TotalSeconds;  // seconds for JWT
            var timestamp = ((long)(utcNow - DateTime.UnixEpoch).TotalMilliseconds).ToString(); // milliseconds
            var path = "/trading-api/v1/users/hmac/login";
            
            // CRITICAL: Message format must be exactly: timestamp + nonce + method + path
            var message = $"{timestamp}{nonce}GET{path}";
            var signature = GenerateHmacSignature(message, _secretKey);

            var request = new HttpRequestMessage(HttpMethod.Get, $"{_hostName}{path}");
            request.Headers.Add("BX-PUBLIC-KEY", _publicKey);
            request.Headers.Add("BX-NONCE", nonce.ToString());
            request.Headers.Add("BX-SIGNATURE", signature);
            request.Headers.Add("BX-TIMESTAMP", timestamp);

            var response = await _httpClient.SendAsync(request);
            var responseBody = await response.Content.ReadAsStringAsync();

            _logger.LogInformation("JWT Generation - HTTP Status: {StatusCode}, Response: {ResponseBody}", 
                response.StatusCode, responseBody);

            if (response.IsSuccessStatusCode)
            {
                var jsonResponse = JsonSerializer.Deserialize<JsonElement>(responseBody);
                return jsonResponse.GetProperty("token").GetString() ?? throw new InvalidOperationException("JWT token not found in response");
            }
            else
            {
                throw new HttpRequestException($"Failed to generate JWT token. Status: {response.StatusCode}, Response: {responseBody}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating JWT token");
            throw;
        }
    }

    /// <summary>
    /// Create a limit order on Bullish Exchange
    /// Step 2: Use JWT token to place order with proper HMAC signature
    /// </summary>
    /// <param name="jwtToken">JWT token from GenerateJwtTokenAsync()</param>
    /// <returns>Order creation response JSON</returns>
    public async Task<string> CreateOrderAsync(string jwtToken)
    {
        try
        {
            // STEP 1: Get server nonce (prevents replay attacks)
            var nonceResponse = await _httpClient.GetAsync($"{_hostName}/trading-api/v1/nonce");
            nonceResponse.EnsureSuccessStatusCode();
            
            var nonceContent = await nonceResponse.Content.ReadAsStringAsync();
            var nonceData = JsonSerializer.Deserialize<JsonElement>(nonceContent);
            // FIX: API returns number, not string - use ToString()
            var nonce = nonceData.GetProperty("lowerBound").ToString();

            // STEP 2: Generate timestamps (CRITICAL: Different precision for different uses)
            var utcNow = DateTime.UtcNow;
            var nextNonce = ((long)(utcNow - DateTime.UnixEpoch).TotalMicroseconds).ToString(); // microseconds for client nonce
            var timestamp = ((long)(utcNow - DateTime.UnixEpoch).TotalMilliseconds).ToString(); // milliseconds for signature

            // STEP 3: Create order body (modify these values for your order)
            var orderBody = new
            {
                symbol = "ETHUSDC",              // Trading pair
                commandType = "V3CreateOrder",   // Required command type
                type = "LIMIT",                  // Order type: LIMIT, MARKET, etc.
                side = "SELL",                   // BUY or SELL
                quantity = "1.123",              // Amount to trade
                price = "1432.6",                // Price per unit (for limit orders)
                timeInForce = "GTC",             // Good Till Cancelled
                allowBorrow = false,             // Margin trading flag
                clientOrderId = nextNonce,       // Unique client identifier
                tradingAccountId = _tradingAccountId
            };

            // STEP 4: Serialize JSON (CRITICAL: Must match Python's compact format)
            var bodyString = JsonSerializer.Serialize(orderBody, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = false  // No pretty printing - compact JSON
            });

            var uri = "/trading-api/v2/orders";
            
            // STEP 5: Create signature payload (CRITICAL: Exact order matters)
            // Format: timestamp + nextNonce + HTTP_METHOD + URI + JSON_BODY
            var payload = $"{timestamp}{nextNonce}POST{uri}{bodyString}";
            var signature = GenerateHmacSignatureFromPayload(payload, _secretKey);

            // Prepare request
            var request = new HttpRequestMessage(HttpMethod.Post, $"{_hostName}{uri}")
            {
                Content = new StringContent(bodyString, Encoding.UTF8, "application/json")
            };

            request.Headers.Add("Authorization", $"Bearer {jwtToken}");
            request.Headers.Add("BX-SIGNATURE", signature);
            request.Headers.Add("BX-TIMESTAMP", timestamp);
            request.Headers.Add("BX-NONCE", nextNonce);
            if (!string.IsNullOrEmpty(_rateLimitToken))
            {
                request.Headers.Add("BX-RATELIMIT-TOKEN", _rateLimitToken);
            }

            // Send request
            var response = await _httpClient.SendAsync(request);
            var responseBody = await response.Content.ReadAsStringAsync();

            _logger.LogInformation("Order Creation - HTTP Status: {StatusCode}, Response: {ResponseBody}", 
                response.StatusCode, responseBody);

            return responseBody;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating order");
            throw;
        }
    }

    /// <summary>
    /// Convenience method: Generate JWT and create order in one call
    /// Use this for simple scenarios
    /// </summary>
    /// <returns>Order creation response JSON</returns>
    public async Task<string> CreateOrderWithAutoJwtAsync()
    {
        var jwtToken = await GenerateJwtTokenAsync();
        return await CreateOrderAsync(jwtToken);
    }

    /// <summary>
    /// Generate HMAC-SHA256 signature for JWT authentication
    /// Used for the initial login request
    /// </summary>
    private static string GenerateHmacSignature(string message, string secretKey)
    {
        var keyBytes = Encoding.UTF8.GetBytes(secretKey);
        var messageBytes = Encoding.UTF8.GetBytes(message);
        var hmacBytes = HMACSHA256.HashData(keyBytes, messageBytes);
        return Convert.ToHexString(hmacBytes).ToLowerInvariant();
    }

    /// <summary>
    /// Generate HMAC-SHA256 signature for order creation
    /// CRITICAL: This matches the Python implementation exactly
    /// 
    /// Process:
    /// 1. SHA256 hash the payload
    /// 2. Convert hash to lowercase hex string  
    /// 3. Convert hex string to bytes
    /// 4. HMAC-SHA256 the hex bytes with secret key
    /// 
    /// This is the KEY FIX that makes order creation work!
    /// </summary>
    private static string GenerateHmacSignatureFromPayload(string payload, string secretKey)
    {
        // Step 1: SHA256 hash the payload
        var payloadBytes = Encoding.UTF8.GetBytes(payload);
        var payloadHash = SHA256.HashData(payloadBytes);
        
        // Step 2: Convert to lowercase hex string
        var payloadHashHex = Convert.ToHexString(payloadHash).ToLowerInvariant();
        
        // Step 3: Convert hex string back to bytes
        var payloadHashHexBytes = Encoding.UTF8.GetBytes(payloadHashHex);
        
        // Step 4: HMAC-SHA256 the hex bytes
        var keyBytes = Encoding.UTF8.GetBytes(secretKey);
        var hmacBytes = HMACSHA256.HashData(keyBytes, payloadHashHexBytes);
        
        return Convert.ToHexString(hmacBytes).ToLowerInvariant();
    }

    /// <summary>
    /// Alternative signature method (not used but kept for reference)
    /// </summary>
    private static string GenerateHmacSignatureFromHash(byte[] hash, string secretKey)
    {
        var keyBytes = Encoding.UTF8.GetBytes(secretKey);
        var hmacBytes = HMACSHA256.HashData(keyBytes, hash);
        return Convert.ToHexString(hmacBytes).ToLowerInvariant();
    }
}