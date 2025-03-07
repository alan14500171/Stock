import { webcrypto } from 'crypto';

if (typeof window === 'undefined') {
  global.crypto = webcrypto;
} else if (!window.crypto) {
  window.crypto = {
    getRandomValues: function(arr) {
      return webcrypto.getRandomValues(arr);
    }
  };
}

export default webcrypto; 