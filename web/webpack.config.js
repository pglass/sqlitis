var path = require('path');

module.exports = {
  entry: ['./static/scripts/jsx/main.jsx'],
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, './static/dist/scripts/js')
  },
  module: {
    rules: [
      { test: /\.jsx$/, exclude: /node_modules/, use: { loader: "babel-loader" }},
      { test: /\.js$/, exclude: /node_modules/, use: { loader: "babel-loader" }},
    ]
  }
};
