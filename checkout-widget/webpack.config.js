const path = require('path');

module.exports = {
  entry: './src/sdk/index.js',
  output: {
    filename: 'checkout.js',
    path: path.resolve(__dirname, 'dist'),
    library: 'PaymentGateway',
    libraryTarget: 'umd',
    globalObject: 'this'
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  mode: 'production',
};