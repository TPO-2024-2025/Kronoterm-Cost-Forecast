import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import css from "rollup-plugin-import-css";

export default {
  input: "src/custom-apex-card.js",
  output: {
    file: "dist/custom-apex-card.js",
    format: "esm",
  },
  treeshake: false,
  plugins: [nodeResolve(), commonjs(), css()],
};
