const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Support .mjs files (needed for some Tamagui internals)
config.resolver.sourceExts.push('mjs');

module.exports = config;
