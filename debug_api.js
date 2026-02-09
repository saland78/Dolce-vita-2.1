// Debug script to test API configuration
const axios = require('axios');

console.log('=== API Debug Test ===');

// Test 1: Check environment variable
console.log('REACT_APP_BACKEND_URL from env:', process.env.REACT_APP_BACKEND_URL);

// Test 2: Create axios instance like in the app
const backendUrl = process.env.REACT_APP_BACKEND_URL || "https://sweettrack-4.preview.emergentagent.com";
console.log('Backend URL used:', backendUrl);

const api = axios.create({
  baseURL: backendUrl,
});

console.log('Axios instance baseURL:', api.defaults.baseURL);

// Test 3: Make a direct request
async function testDirectRequest() {
  try {
    console.log('\n=== Testing Direct HTTPS Request ===');
    const response = await axios.get('https://sweettrack-4.preview.emergentagent.com/api/orders/stats');
    console.log('✅ Direct HTTPS request successful:', response.status);
    console.log('Response data:', response.data);
  } catch (error) {
    console.log('❌ Direct HTTPS request failed:', error.message);
  }
}

// Test 4: Make request using axios instance
async function testInstanceRequest() {
  try {
    console.log('\n=== Testing Axios Instance Request ===');
    const response = await api.get('/api/orders/stats');
    console.log('✅ Axios instance request successful:', response.status);
    console.log('Response data:', response.data);
  } catch (error) {
    console.log('❌ Axios instance request failed:', error.message);
  }
}

// Run tests
testDirectRequest();
testInstanceRequest();