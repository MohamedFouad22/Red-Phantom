const errorHandler = (err, req, res, next) => {
  console.error(err);

  res.status(500).json({
    success: false,
    msg: "Server Error",
    error: err.message
  });
};

export default errorHandler;
